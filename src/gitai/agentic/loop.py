"""Agentic loop orchestrator for tool-calling LLM interactions."""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import click

from gitai.agentic.tools import DiffInspectionTools, ToolCall, ToolResult
from gitai.core.models import DiffAnalysis
from gitai.providers.base import BaseProvider
from gitai.utils.logger import log_with_context, setup_logger


@dataclass
class AgenticResult:
    """Result of an agentic loop execution."""

    content: str
    model_used: str
    iterations: int
    tool_calls_made: List[Dict[str, Any]] = field(default_factory=list)
    total_tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AgenticLoop:
    """Orchestrates the tool-calling agentic loop.

    Flow:
    1. Send initial system + user message with tool definitions
    2. If model returns tool_calls, execute them and append results
    3. Repeat until model returns text without tool_calls or max_iterations
    4. Return the final text content
    """

    MAX_ITERATIONS = 10

    def __init__(
        self,
        provider: BaseProvider,
        diff_analysis: DiffAnalysis,
        max_iterations: int = 10,
        tracer: Optional[Any] = None,
    ) -> None:
        self.provider = provider
        self.tools = DiffInspectionTools(diff_analysis)
        self.max_iterations = min(max_iterations, self.MAX_ITERATIONS)
        self.tracer = tracer
        self.logger = setup_logger(__name__)

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AgenticResult:
        """Run the agentic loop.

        Args:
            system_prompt: System instructions for the model.
            user_prompt: User message (rendered template).
            temperature: Sampling temperature.
            max_tokens: Max tokens per LLM call.

        Returns:
            AgenticResult with the final commit message and metadata.
        """
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        tool_definitions = DiffInspectionTools.get_tool_definitions()
        tool_calls_log: List[Dict[str, Any]] = []
        total_tokens = 0

        if self.tracer:
            self.tracer.start_trace(
                command="commit",
                metadata={
                    "mode": "agentic",
                    "max_iterations": self.max_iterations,
                    "provider": self.provider.get_provider_name(),
                },
            )

        try:
            click.echo(click.style("\n--- Agentic Mode ---", fg="cyan", bold=True))

            for iteration in range(self.max_iterations):
                click.echo(
                    click.style(
                        f"\n[Iteration {iteration + 1}/{self.max_iterations}] ",
                        fg="cyan",
                    )
                    + "Thinking..."
                )

                log_with_context(
                    self.logger,
                    "info",
                    "Agentic loop iteration",
                    iteration=iteration,
                    messages_count=len(messages),
                )

                # Trace LLM call start
                if self.tracer:
                    self.tracer.start_llm_span(iteration, messages)

                start_time = time.time()
                response = self.provider.chat_with_tools(
                    messages=messages,
                    tools=tool_definitions,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency_ms = (time.time() - start_time) * 1000

                # Trace LLM call end
                if self.tracer:
                    self.tracer.end_llm_span(response, latency_ms)

                tokens = response.get("tokens_used") or 0
                total_tokens += tokens

                raw_tool_calls = response.get("tool_calls", [])

                if not raw_tool_calls:
                    # Model returned final text — done
                    content = response.get("content", "").strip()

                    click.echo(
                        click.style(
                            f"\nDone — {iteration + 1} iterations, "
                            f"{len(tool_calls_log)} tool calls",
                            fg="cyan",
                        )
                    )
                    click.echo(click.style("---\n", fg="cyan"))

                    log_with_context(
                        self.logger,
                        "info",
                        "Agentic loop completed",
                        iterations=iteration + 1,
                        tool_calls_total=len(tool_calls_log),
                        content_length=len(content),
                    )

                    return AgenticResult(
                        content=content,
                        model_used=response.get("model", "unknown"),
                        iterations=iteration + 1,
                        tool_calls_made=tool_calls_log,
                        total_tokens_used=total_tokens,
                    )

                # Model wants to call tools — build assistant message
                assistant_msg: Dict[str, Any] = {"role": "assistant"}
                content = response.get("content")
                if content:
                    assistant_msg["content"] = content

                # Build tool_calls in OpenAI format for the message history
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in raw_tool_calls
                ]
                messages.append(assistant_msg)

                # Execute each tool call
                for tc_data in raw_tool_calls:
                    tool_call = ToolCall(
                        id=tc_data["id"],
                        name=tc_data["name"],
                        arguments=tc_data["arguments"],
                    )

                    # User-facing: show which tool is being called
                    args_display = ""
                    if tool_call.arguments:
                        args_display = ", ".join(
                            f"{k}={v}" for k, v in tool_call.arguments.items()
                        )
                    click.echo(
                        click.style("  -> ", fg="yellow")
                        + click.style(tool_call.name, fg="yellow", bold=True)
                        + (f"({args_display})" if args_display else "()")
                    )

                    # Trace tool execution
                    if self.tracer:
                        self.tracer.start_tool_span(tool_call)

                    tool_start = time.time()
                    result = self.tools.execute(tool_call)
                    tool_latency = (time.time() - tool_start) * 1000

                    if self.tracer:
                        self.tracer.end_tool_span(result, tool_latency)

                    tool_calls_log.append({
                        "iteration": iteration,
                        "tool": tool_call.name,
                        "arguments": tool_call.arguments,
                        "result_preview": result.content[:200],
                        "is_error": result.is_error,
                    })

                    # User-facing: show tool result summary
                    if result.is_error:
                        click.echo(
                            click.style("     ERROR: ", fg="red")
                            + result.content[:120]
                        )
                    elif tool_call.name == "list_changed_files":
                        # Show the full file list for visibility
                        click.echo(
                            click.style("     ", fg="green") + result.content
                        )
                    elif tool_call.name == "get_file_diff":
                        diff_lines = result.content.count("\n") + 1
                        click.echo(
                            click.style("     OK ", fg="green")
                            + f"({diff_lines} lines)"
                        )
                    elif tool_call.name == "get_change_summary":
                        click.echo(
                            click.style("     ", fg="green") + result.content
                        )
                    else:
                        click.echo(
                            click.style("     OK ", fg="green")
                            + f"({len(result.content)} chars)"
                        )

                    log_with_context(
                        self.logger,
                        "info",
                        "Tool executed",
                        tool=tool_call.name,
                        is_error=result.is_error,
                        result_length=len(result.content),
                    )

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result.tool_call_id,
                        "content": result.content,
                    })

            # Max iterations reached — force a final response without tools
            log_with_context(
                self.logger,
                "warning",
                "Max iterations reached, forcing final response",
                max_iterations=self.max_iterations,
            )

            messages.append({
                "role": "user",
                "content": (
                    "You have used all available iterations. "
                    "Please provide your final commit message now "
                    "based on the information you have gathered."
                ),
            })

            if self.tracer:
                self.tracer.start_llm_span(self.max_iterations, messages)

            start_time = time.time()
            final_response = self.provider.chat_with_tools(
                messages=messages,
                tools=[],  # No tools — force text response
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency_ms = (time.time() - start_time) * 1000

            if self.tracer:
                self.tracer.end_llm_span(final_response, latency_ms)

            tokens = final_response.get("tokens_used") or 0
            total_tokens += tokens

            return AgenticResult(
                content=final_response.get("content", "").strip(),
                model_used=final_response.get("model", "unknown"),
                iterations=self.max_iterations,
                tool_calls_made=tool_calls_log,
                total_tokens_used=total_tokens,
                metadata={"max_iterations_reached": True},
            )

        finally:
            if self.tracer:
                self.tracer.end_trace()

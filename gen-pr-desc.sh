#!/usr/bin/env bash
set -euo pipefail

# ================================================
# Improved PR Description Generator
# 
# Features:
# - Outputs to stdout by default (no file creation)
# - Optional file output with --output-file flag
# - External prompt files for maintainability
# - Optional validation step with --validate flag
# - Cleaner structure and error handling
# ================================================

# Default configuration
#MODEL="${MODEL:-llama3.1}"
#VALIDATOR_MODEL="${VALIDATOR_MODEL:-qwen2.5:7b}"
MODEL="${MODEL:-qwen2.5:7b}"
VALIDATOR_MODEL="${VALIDATOR_MODEL:-qwen2.5:7b}"
OUTFILE=""
OUTPUT_TO_STDOUT=true
MAX_DIFF_LINES="${MAX_DIFF_LINES:-5000}"
TEMPERATURE="${TEMPERATURE:-0.4}"
NUM_CTX="${NUM_CTX:-8192}"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="${SCRIPT_DIR}/prompts"

# Parse command line options
VALIDATE_MODE=false
while [[ $# -gt 0 ]]; do
  case $1 in
    --validate)
      VALIDATE_MODE=true
      shift
      ;;
    --output-file|-o)
      if [[ -n "${2:-}" ]]; then
        OUTFILE="$2"
        OUTPUT_TO_STDOUT=false
        shift 2
      else
        error "--output-file requires a filename argument"
      fi
      ;;
    --help|-h)
      echo "Usage: $0 [--validate] [--output-file FILE] [--help]"
      echo ""
      echo "By default, outputs the PR description to stdout (terminal)."
      echo ""
      echo "Options:"
      echo "  --validate         Enable validation step with second LLM"
      echo "  --output-file, -o  Save output to specified file instead of stdout"
      echo "  --help, -h         Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  MODEL                 Primary LLM model (default: llama3.1)"
      echo "  VALIDATOR_MODEL       Validation LLM model (default: llama3.1)"
      echo "  MAX_DIFF_LINES       Max diff lines to process (default: 4000)"
      echo "  NUM_CTX              Context window size (default: 8192)"
      echo "  TEMPERATURE      Model temperature for conciseness (default: 0.4)"
      exit 0
      ;;
    *)
      error "Unknown option: $1. Use --help for usage information."
      ;;
  esac
done

export LC_ALL=C

# ========================================
# Utility Functions
# ========================================

log() {
    echo "› $*"
}

error() {
    echo "ERROR: $*" >&2
    exit 1
}

check_dependencies() {
    command -v git >/dev/null 2>&1 || error "git is not installed or not in PATH"
    command -v ollama >/dev/null 2>&1 || error "ollama is not installed or not in PATH"
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || error "not inside a git repository"
    
    [[ -f "${PROMPTS_DIR}/pr-generation.txt" ]] || error "pr-generation.txt prompt file not found in ${PROMPTS_DIR}"
    
    if [[ "$VALIDATE_MODE" == "true" ]]; then
        [[ -f "${PROMPTS_DIR}/pr-validation.txt" ]] || error "pr-validation.txt prompt file not found in ${PROMPTS_DIR}"
    fi
}

get_git_context() {
    log "Fetching remote refs..."
    git fetch origin --quiet
    
    CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    REPO_NAME="$(basename -s .git "$(git config --get remote.origin.url || echo 'repo')")"
    GIT_USER="$(git config user.name || echo 'unknown')"
    GIT_EMAIL="$(git config user.email || echo 'unknown@example.com')"
    
    DIFF="$(git diff origin/main || true)"
    if [[ -z "${DIFF}" ]]; then
        log "No differences against origin/main. Nothing to describe."
        exit 0
    fi
    
    DIFF_LINES=$(printf "%s\n" "$DIFF" | wc -l | awk '{print $1}')
    TRUNCATED="false"
    if (( DIFF_LINES > MAX_DIFF_LINES )); then
        DIFF="$(printf "%s\n" "$DIFF" | head -n "${MAX_DIFF_LINES}")"
        TRUNCATED="true"
        log "Diff truncated to ${MAX_DIFF_LINES} lines (was ${DIFF_LINES})"
    fi
    
    CHANGED_FILES="$(git diff --name-status origin/main | sed 's/^/- /')"
}

build_ollama_command() {
    local model="$1"
    local cmd=(ollama run)
    
    if ollama --help 2>/dev/null | grep -q -- '--num_ctx'; then
        cmd+=(--num_ctx "$NUM_CTX")
    fi
    if ollama --help 2>/dev/null | grep -q -- '--temperature'; then
        cmd+=(--temperature "$TEMPERATURE")
    fi
    
    cmd="$cmd $model"
    
    echo "$cmd"
}

generate_pr_description() {
    log "Generating PR description with ${MODEL}..."
    
    local prompt_file
    prompt_file="$(mktemp -t pr_prompt.XXXXXX)"
    
    # Build complete prompt
    {
        cat "${PROMPTS_DIR}/pr-generation.txt"
        echo ""
        echo "--- CONTEXTO DEL REPO ---"
        echo "Repositorio: ${REPO_NAME}"
        echo "Rama actual: ${CURRENT_BRANCH}"
        echo "Autor local: ${GIT_USER} <${GIT_EMAIL}>"
        echo ""
        echo "Archivos cambiados (name-status):"
        echo "${CHANGED_FILES}"
        echo ""
        echo "¿Diff truncado?: ${TRUNCATED}"
        echo ""
        echo "--- DIFF (contra origin/main) ---"
        printf "%s\n" "$DIFF"
    } > "$prompt_file"
    
    # Execute command
    local cmd_array
    IFS=$'\n' read -r -d '' -a cmd_array < <(build_ollama_command "$MODEL" && printf '\0')
    
    local response
    response="$("${cmd_array[@]}" < "$prompt_file")"
    
    # Store response for potential validation
    GENERATED_RESPONSE="$response"
    
    if [[ "$OUTPUT_TO_STDOUT" == "true" ]]; then
        # Don't output here if validation is enabled - let validate function handle it
        if [[ "$VALIDATE_MODE" != "true" ]]; then
            printf "%s\n" "$response"
        fi
        log "PR description generated"
    else
        printf "%s\n" "$response" > "$OUTFILE"
        log "PR description generated: $OUTFILE"
    fi
    
    rm -f "$prompt_file"
}

validate_pr_description() {
    if [[ "$VALIDATE_MODE" != "true" ]]; then
        return 0
    fi
    
    log "Validating/correcting with ${VALIDATOR_MODEL}..."
    
    local temp_input temp_output
    temp_input="$(mktemp -t pr_validation_input.XXXXXX)"
    temp_output="$(mktemp -t pr_validation_output.XXXXXX)"
    
    # Build validation prompt
    {
        cat "${PROMPTS_DIR}/pr-validation.txt"
        echo ""
        printf "%s\n" "$GENERATED_RESPONSE"
    } > "$temp_input"
    
    # Execute validation
    local cmd_array
    IFS=$'\n' read -r -d '' -a cmd_array < <(build_ollama_command "$VALIDATOR_MODEL" && printf '\0')
    
    local validated_response
    validated_response="$("${cmd_array[@]}" < "$temp_input")"
    
    if [[ "$OUTPUT_TO_STDOUT" == "true" ]]; then
        printf "%s\n" "$validated_response"
        log "PR description validated and output to stdout"
    else
        printf "%s\n" "$validated_response" > "$OUTFILE"
        log "PR description validated and updated: $OUTFILE"
    fi
    
    rm -f "$temp_input" "$temp_output"
}

cleanup() {
    # Clean up any remaining temporary files
    rm -f /tmp/pr_prompt.* /tmp/pr_validation_*
}

# ========================================
# Main Execution
# ========================================

main() {
    trap cleanup EXIT
    
    check_dependencies
    get_git_context
    generate_pr_description
    validate_pr_description
    
    log "✅ Process completed successfully!"
    
    if [[ "$OUTPUT_TO_STDOUT" == "true" ]]; then
        log "Output sent to stdout (terminal)"
    else
        log "Output file: $OUTFILE"
    fi
    
    if [[ "$VALIDATE_MODE" == "true" ]]; then
        log "Note: Validation was applied"
    else
        log "Note: Run with --validate flag to enable validation step"
    fi
}

# Run main function
main "$@"

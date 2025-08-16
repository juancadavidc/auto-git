#!/usr/bin/env bash
set -euo pipefail

# ================================================
# Improved PR Description Generator (Gemini)
# 
# Features:
# - Outputs to stdout by default (no file creation)
# - Optional file output with --output-file flag
# - External prompt files for maintainability
# - Optional validation step with --validate flag
# - Cleaner structure and error handling
# - Uses Google Gemini API instead of local models
# ================================================

# Default configuration
MODEL="${MODEL:-gemini-1.5-flash}"
VALIDATOR_MODEL="${VALIDATOR_MODEL:-gemini-1.5-flash}"
OUTFILE=""
OUTPUT_TO_STDOUT=true
MAX_DIFF_LINES="${MAX_DIFF_LINES:-5000}"
TEMPERATURE="${TEMPERATURE:-0.4}"

# API Configuration
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
GEMINI_API_URL="${GEMINI_API_URL:-https://generativelanguage.googleapis.com/v1beta/models}"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="${SCRIPT_DIR}/prompts"

# Parse command line options
VALIDATE_MODE=false
VERBOSE=false
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
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--validate] [--output-file FILE] [--verbose] [--help]"
      echo ""
      echo "By default, outputs the PR description to stdout (terminal)."
      echo ""
      echo "Options:"
      echo "  --validate         Enable validation step with second LLM"
      echo "  --output-file, -o  Save output to specified file instead of stdout"
      echo "  --verbose, -v      Show detailed API execution information"
      echo "  --help, -h         Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  GEMINI_API_KEY      Google Gemini API key (required)"
      echo "  MODEL               Primary Gemini model (default: gemini-1.5-flash)"
      echo "  VALIDATOR_MODEL     Validation Gemini model (default: gemini-1.5-flash)"
      echo "  MAX_DIFF_LINES      Max diff lines to process (default: 5000)"
      echo "  TEMPERATURE         Model temperature for conciseness (default: 0.4)"
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
    command -v curl >/dev/null 2>&1 || error "curl is not installed or not in PATH"
    command -v jq >/dev/null 2>&1 || error "jq is not installed or not in PATH (required for JSON processing)"
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || error "not inside a git repository"
    
    [[ -f "${PROMPTS_DIR}/pr-generation.txt" ]] || error "pr-generation.txt prompt file not found in ${PROMPTS_DIR}"
    
    if [[ "$VALIDATE_MODE" == "true" ]]; then
        [[ -f "${PROMPTS_DIR}/pr-validation.txt" ]] || error "pr-validation.txt prompt file not found in ${PROMPTS_DIR}"
    fi
    
    # Check for API key
    if [[ -z "$GEMINI_API_KEY" ]]; then
        error "GEMINI_API_KEY environment variable is required. Get your API key from https://makersuite.google.com/app/apikey"
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

escape_json_string() {
    local input="$1"
    # Escape backslashes, quotes, and newlines for JSON
    printf '%s' "$input" | sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "%s\\n", $0}' | sed 's/\\n$//'
}

call_gemini_api() {
    local prompt="$1"
    local model="$2"
    local temp_request_file temp_response_file
    
    temp_request_file="$(mktemp "/tmp/gemini_request.XXXXXX")"
    temp_response_file="$(mktemp "/tmp/gemini_response.XXXXXX")"
    
    # Escape the prompt for JSON
    local escaped_prompt
    escaped_prompt="$(escape_json_string "$prompt")"
    
    # Create the JSON request
    cat > "$temp_request_file" << EOF
{
  "contents": [{
    "parts": [{
      "text": "$escaped_prompt"
    }]
  }],
  "generationConfig": {
    "temperature": $TEMPERATURE,
    "topK": 1,
    "topP": 1,
    "maxOutputTokens": 4096
  }
}
EOF

    if [[ "$VERBOSE" == "true" ]]; then
        log "Request file: $temp_request_file"
        log "Making API call to: ${GEMINI_API_URL}/${model}:generateContent"
    fi
    
    # Make the API call
    local http_status
    http_status=$(curl -s -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -H "x-goog-api-key: $GEMINI_API_KEY" \
        -d "@$temp_request_file" \
        "${GEMINI_API_URL}/${model}:generateContent" \
        -o "$temp_response_file")
    
    if [[ "$VERBOSE" == "true" ]]; then
        log "HTTP Status: $http_status"
        log "Response file: $temp_response_file"
        log "Response content:"
        cat "$temp_response_file"
        echo ""
    fi
    
    local success=false
    local response_text=""
    
    if [[ "$http_status" == "200" ]]; then
        # Extract the text from the response
        if command -v jq >/dev/null 2>&1; then
            response_text="$(jq -r '.candidates[0].content.parts[0].text // empty' "$temp_response_file" 2>/dev/null)"
            if [[ -n "$response_text" && "$response_text" != "null" ]]; then
                success=true
            fi
        fi
    fi
    
    # Clean up temp files
    rm -f "$temp_request_file" "$temp_response_file"
    
    if [[ "$success" == "true" ]]; then
        echo "$response_text"
        return 0
    else
        return 1
    fi
}

generate_pr_description() {
    log "Generating PR description with Gemini ${MODEL}..."
    
    # Build complete prompt
    local complete_prompt
    complete_prompt="$(cat "${PROMPTS_DIR}/pr-generation.txt")

--- CONTEXTO DEL REPO ---
Repositorio: ${REPO_NAME}
Rama actual: ${CURRENT_BRANCH}
Autor local: ${GIT_USER} <${GIT_EMAIL}>

Archivos cambiados (name-status):
${CHANGED_FILES}

¿Diff truncado?: ${TRUNCATED}

--- DIFF (contra origin/main) ---
${DIFF}"

    if [[ "$VERBOSE" == "true" ]]; then
        log "Verbose mode: showing prompt content preview"
        echo "----------------------------------------"
        echo "PROMPT PREVIEW (first 20 lines):"
        echo "----------------------------------------"
        echo "$complete_prompt" | head -n 20
        echo "----------------------------------------"
        local total_lines
        total_lines=$(echo "$complete_prompt" | wc -l)
        log "Total prompt lines: $total_lines"
        log "Model: $MODEL | Temperature: $TEMPERATURE"
    fi
    
    log "Calling Gemini API..."
    
    # Try API call with error handling
    local response=""
    local api_success=false
    
    if [[ "$VERBOSE" == "true" ]]; then
        log "Starting API call (verbose mode - showing response)..."
        echo "======== API RESPONSE START ========"
        if response="$(call_gemini_api "$complete_prompt" "$MODEL")"; then
            api_success=true
            echo "$response"
            echo "======== API RESPONSE END ========"
            log "API response received successfully"
        else
            echo "======== API RESPONSE END (FAILED) ========"
            log "API call failed"
            api_success=false
        fi
    else
        if response="$(call_gemini_api "$complete_prompt" "$MODEL" 2>/dev/null)"; then
            api_success=true
            log "API response received"
        else
            log "API call failed"
            api_success=false
        fi
    fi
    
    if [[ "$api_success" != "true" || -z "$response" ]]; then
        error "Failed to generate PR description. Please check your API key and internet connection."
    fi
    
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
}

validate_pr_description() {
    if [[ "$VALIDATE_MODE" != "true" ]]; then
        return 0
    fi
    
    log "Validating/correcting with Gemini ${VALIDATOR_MODEL}..."
    
    # Build validation prompt
    local complete_prompt
    complete_prompt="$(cat "${PROMPTS_DIR}/pr-validation.txt")

${GENERATED_RESPONSE}"
    
    if [[ "$VERBOSE" == "true" ]]; then
        log "Validation prompt preview (first 10 lines):"
        echo "----------------------------------------"
        echo "$complete_prompt" | head -n 10
        echo "----------------------------------------"
    fi
    
    log "Calling Gemini API for validation..."
    
    # Execute validation
    local validated_response=""
    local api_success=false
    
    if [[ "$VERBOSE" == "true" ]]; then
        log "Starting validation API call (verbose mode)..."
        echo "======== VALIDATION API RESPONSE START ========"
        if validated_response="$(call_gemini_api "$complete_prompt" "$VALIDATOR_MODEL")"; then
            api_success=true
            echo "$validated_response"
            echo "======== VALIDATION API RESPONSE END ========"
            log "Validation API response received successfully"
        else
            echo "======== VALIDATION API RESPONSE END (FAILED) ========"
            log "Validation API call failed, using original response"
            api_success=false
        fi
    else
        if validated_response="$(call_gemini_api "$complete_prompt" "$VALIDATOR_MODEL" 2>/dev/null)"; then
            api_success=true
            log "Validation API response received"
        else
            log "Validation API call failed, using original response"
            api_success=false
        fi
    fi
    
    # Use validated response if successful, otherwise fall back to original
    if [[ "$api_success" == "true" && -n "$validated_response" ]]; then
        if [[ "$OUTPUT_TO_STDOUT" == "true" ]]; then
            printf "%s\n" "$validated_response"
            log "PR description validated and output to stdout"
        else
            printf "%s\n" "$validated_response" > "$OUTFILE"
            log "PR description validated and updated: $OUTFILE"
        fi
    else
        log "Validation failed, using original response"
        if [[ "$OUTPUT_TO_STDOUT" == "true" ]]; then
            printf "%s\n" "$GENERATED_RESPONSE"
            log "Original PR description output to stdout"
        else
            printf "%s\n" "$GENERATED_RESPONSE" > "$OUTFILE"
            log "Original PR description saved: $OUTFILE"
        fi
    fi
}

cleanup() {
    # Clean up any remaining temporary files
    rm -f /tmp/gemini_request.*
    rm -f /tmp/gemini_response.*
    rm -f /tmp/pr_prompt.*
    rm -f /tmp/pr_validation_*
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

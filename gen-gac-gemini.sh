#!/usr/bin/env bash
set -euo pipefail

# ================================================
# Git Add & Commit with AI-Generated Message (Gemini)
# 
# Features:
# - Stages all changes with git add .
# - Optionally creates and switches to a new branch
# - Reviews staged changes and generates commit message
# - Uses external prompt file for maintainability
# - Clean structure and error handling
# - Uses Google Gemini API instead of local models
# ================================================

# Default configuration
MODEL="${MODEL:-gemini-1.5-flash}"
MAX_DIFF_LINES="${MAX_DIFF_LINES:-5000}"
TEMPERATURE="${TEMPERATURE:-0.4}"
NEW_BRANCH=""
DRY_RUN=false
VERBOSE=false

# API Configuration
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
GEMINI_API_URL="${GEMINI_API_URL:-https://generativelanguage.googleapis.com/v1beta/models}"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="${SCRIPT_DIR}/prompts"

# Parse command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch|-b)
      if [[ -n "${2:-}" ]]; then
        NEW_BRANCH="$2"
        shift 2
      else
        error "--branch requires a branch name argument"
      fi
      ;;
    --dry-run|-d)
      DRY_RUN=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--branch BRANCH_NAME] [--dry-run] [--verbose] [--help]"
      echo ""
      echo "Stages all changes and generates an AI commit message using Google Gemini."
      echo ""
      echo "Options:"
      echo "  --branch, -b     Create and switch to new branch before staging"
      echo "  --dry-run, -d    Show what would be done without making changes"
      echo "  --verbose, -v    Show detailed API execution information"
      echo "  --help, -h       Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  GEMINI_API_KEY   Google Gemini API key (required)"
      echo "  MODEL            Gemini model for commit message generation (default: gemini-1.5-flash)"
      echo "  MAX_DIFF_LINES   Max diff lines to process (default: 5000)"
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
    command -v curl >/dev/null 2>&1 || error "curl is not installed or not in PATH"
    command -v jq >/dev/null 2>&1 || error "jq is not installed or not in PATH (required for JSON processing)"
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || error "not inside a git repository"
    
    [[ -f "${PROMPTS_DIR}/commit-generation.txt" ]] || error "commit-generation.txt prompt file not found in ${PROMPTS_DIR}"
    
    # Check for API key
    if [[ -z "$GEMINI_API_KEY" ]]; then
        error "GEMINI_API_KEY environment variable is required. Get your API key from https://makersuite.google.com/app/apikey"
    fi
}

create_new_branch() {
    if [[ -z "$NEW_BRANCH" ]]; then
        return 0
    fi
    
    log "Creating and switching to new branch: $NEW_BRANCH"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would run: git checkout -b $NEW_BRANCH"
        return 0
    fi
    
    # Check if branch already exists
    if git rev-parse --verify "$NEW_BRANCH" >/dev/null 2>&1; then
        error "Branch '$NEW_BRANCH' already exists"
    fi
    
    git checkout -b "$NEW_BRANCH"
}

stage_changes() {
    log "Staging all changes..."
    
    # Check if there are any changes to stage
    if ! git diff-index --quiet HEAD --; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log "[DRY RUN] Would run: git add ."
            log "[DRY RUN] Changes that would be staged:"
            git status --porcelain
            return 0
        fi
        
        git add .
        log "Changes staged successfully"
    else
        log "No changes to stage"
        exit 0
    fi
}

get_staged_diff() {
    local diff
    
    if [[ "$DRY_RUN" == "true" ]]; then
        # For dry run, simulate what would be staged
        diff="$(git diff HEAD)"
        if [[ -z "$diff" ]]; then
            log "No changes would be staged"
            exit 0
        fi
    else
        diff="$(git diff --cached)"
        if [[ -z "$diff" ]]; then
            error "No staged changes found. Run 'git add' first or make sure there are changes to commit."
        fi
    fi
    
    local diff_lines
    diff_lines=$(printf "%s\n" "$diff" | wc -l | awk '{print $1}')
    
    TRUNCATED="false"
    if (( diff_lines > MAX_DIFF_LINES )); then
        diff="$(printf "%s\n" "$diff" | head -n "${MAX_DIFF_LINES}")"
        TRUNCATED="true"
        log "Diff truncated to ${MAX_DIFF_LINES} lines (was ${diff_lines})"
    fi
    
    STAGED_DIFF="$diff"
}

escape_json_string() {
    local input="$1"
    # Escape backslashes, quotes, and newlines for JSON
    printf '%s' "$input" | sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "%s\\n", $0}' | sed 's/\\n$//'
}

call_gemini_api() {
    local prompt="$1"
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
    "maxOutputTokens": 1024
  }
}
EOF

    if [[ "$VERBOSE" == "true" ]]; then
        log "Request file: $temp_request_file"
        log "Making API call to: ${GEMINI_API_URL}/${MODEL}:generateContent"
    fi
    
    # Make the API call
    local http_status
    http_status=$(curl -s -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -H "x-goog-api-key: $GEMINI_API_KEY" \
        -d "@$temp_request_file" \
        "${GEMINI_API_URL}/${MODEL}:generateContent" \
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

generate_commit_message() {
    log "Generating commit message with Gemini ${MODEL}..."
    
    # Load the prompt from the prompt file
    local prompt_template
    prompt_template="$(cat "${PROMPTS_DIR}/commit-generation.txt")"
    
    # Get the git diff for staged changes
    local git_diff
    if [[ "$DRY_RUN" == "true" ]]; then
        git_diff="$(git diff HEAD)"
    else
        git_diff="$(git diff --cached)"
    fi
    
    # Get list of modified and added files
    local files_status
    if [[ "$DRY_RUN" == "true" ]]; then
        files_status="$(git status --porcelain)"
    else
        files_status="$(git diff --cached --name-status)"
    fi
    
    # Build the complete prompt
    local complete_prompt
    complete_prompt="$prompt_template

FILES MODIFIED/ADDED:
$files_status

GIT DIFF:
$git_diff"

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
        if response="$(call_gemini_api "$complete_prompt")"; then
            api_success=true
            echo "$response"
            echo "======== API RESPONSE END ========"
            log "API response received successfully"
        else
            echo "======== API RESPONSE END (FAILED) ========"
            log "API call failed, using fallback"
            api_success=false
        fi
    else
        if response="$(call_gemini_api "$complete_prompt" 2>/dev/null)"; then
            api_success=true
            log "API response received"
        else
            log "API call failed, using fallback"
            api_success=false
        fi
    fi
    
    if [[ "$api_success" == "true" && -n "$response" ]]; then
        # Extract the first line that looks like a conventional commit
        COMMIT_MESSAGE="$(echo "$response" | grep -E '^[a-z]+(\([^)]+\))?: .+' | head -n 1)"
        if [[ -z "$COMMIT_MESSAGE" ]]; then
            # If no conventional format found, take the first non-empty line
            COMMIT_MESSAGE="$(echo "$response" | grep -v '^[[:space:]]*$' | head -n 1)"
        fi
    else
        log "API did not respond or failed, using fallback"
        COMMIT_MESSAGE=""
    fi
    
    # If no conventional format found, create a smart fallback
    if [[ -z "$COMMIT_MESSAGE" ]]; then
        log "Creating intelligent fallback commit message..."

        
        
        # Analyze the changes to determine type and description
        local change_type="chore"
        local description="update project files"
        
        # Check for new files
        local new_files
        new_files="$(git diff --cached --name-status | grep '^A' | wc -l | tr -d ' ')"
        local modified_files  
        modified_files="$(git diff --cached --name-status | grep '^M' | wc -l | tr -d ' ')"
        local deleted_files
        deleted_files="$(git diff --cached --name-status | grep '^D' | wc -l | tr -d ' ')"
        
        # Analyze file types and content
        if git diff --cached --name-only | grep -qE '\.(md|txt|rst|doc)$'; then
            change_type="docs"
            description="update documentation"
        elif git diff --cached --name-only | grep -qE '\.(sh|bash)$'; then
            if [[ "$new_files" -gt 0 ]]; then
                change_type="feat"
                description="add shell scripts"
            else
                change_type="fix"
                description="update shell scripts"
            fi
        elif git diff --cached --name-only | grep -qE '\.(js|ts|py|go|java|c|cpp|rs)$'; then
            if git diff --cached | grep -q '^+.*test\|^+.*spec\|^+.*Test'; then
                change_type="test"
                description="add tests"
            elif git diff --cached | grep -q '^+.*function\|^+.*class\|^+.*def \|^+.*fn '; then
                change_type="feat"
                description="add new functionality"
            else
                change_type="fix"
                description="update code"
            fi
        elif git diff --cached --name-only | grep -qE '\.(css|scss|sass|less)$'; then
            change_type="style"
            description="update styles"
        elif git diff --cached --name-only | grep -qE '\.(json|yaml|yml|toml|ini|conf)$'; then
            change_type="chore"
            description="update configuration"
        fi
        
        # Adjust description based on file operations
        if [[ "$new_files" -gt 0 && "$modified_files" -eq 0 && "$deleted_files" -eq 0 ]]; then
            description="${description/update/add}"
        elif [[ "$deleted_files" -gt 0 && "$new_files" -eq 0 && "$modified_files" -eq 0 ]]; then
            description="${description/update/remove}"
            description="${description/add/remove}"
        fi
        
        COMMIT_MESSAGE="$change_type: $description"
        log "Generated fallback commit message: $COMMIT_MESSAGE"
    fi
    
    # Final cleanup - trim whitespace but allow up to 72 characters
    COMMIT_MESSAGE="$(echo "$COMMIT_MESSAGE" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | cut -c1-72)"
}

show_commit_preview() {
    echo ""
    echo "================================================"
    echo "Generated Commit Message:"
    echo "================================================"
    printf "%s\n" "$COMMIT_MESSAGE"
    echo "================================================"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would commit with the above message"
        return 0
    fi
    
    read -p "Commit with this message? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git commit -m "$COMMIT_MESSAGE"
        log "✅ Changes committed successfully!"
    else
        log "Commit cancelled. Changes remain staged."
        echo "To commit manually, use: git commit -m \"<your message>\""
        echo "To unstage changes, use: git reset"
    fi
}

cleanup() {
    # Clean up any remaining temporary files
    rm -f /tmp/gemini_request.*
    rm -f /tmp/gemini_response.*
}

# ========================================
# Main Execution
# ========================================

main() {
    trap cleanup EXIT
    
    check_dependencies
    create_new_branch
    stage_changes
    get_staged_diff
    generate_commit_message
    show_commit_preview
    
    log "✅ Process completed successfully!"
}


# ========================================
# Main Execution
# ========================================

main "$@"



#!/usr/bin/env bash
set -euo pipefail

# ================================================
# Git Add & Commit with AI-Generated Message
# 
# Features:
# - Stages all changes with git add .
# - Optionally creates and switches to a new branch
# - Reviews staged changes and generates commit message
# - Uses external prompt file for maintainability
# - Clean structure and error handling
# ================================================

# Default configuration
MODEL="${MODEL:-llama3.1}"
NUM_CTX="${NUM_CTX:-8192}"
MAX_DIFF_LINES="${MAX_DIFF_LINES:-2000}"
NEW_BRANCH=""
DRY_RUN=false

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
    --help|-h)
      echo "Usage: $0 [--branch BRANCH_NAME] [--dry-run] [--help]"
      echo ""
      echo "Stages all changes and generates an AI commit message."
      echo ""
      echo "Options:"
      echo "  --branch, -b     Create and switch to new branch before staging"
      echo "  --dry-run, -d    Show what would be done without making changes"
      echo "  --help, -h       Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  MODEL            LLM model for commit message generation (default: llama3.1)"
      echo "  MAX_DIFF_LINES   Max diff lines to process (default: 2000)"
      echo "  NUM_CTX          Context window size (default: 8192)"
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
    
    [[ -f "${PROMPTS_DIR}/commit-generation.txt" ]] || error "commit-generation.txt prompt file not found in ${PROMPTS_DIR}"
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

build_ollama_command() {
    local model="$1"
    local cmd="ollama run"
    
    if ollama --help 2>/dev/null | grep -q -- '--num_ctx'; then
        cmd="$cmd --num_ctx $NUM_CTX"
    fi
    cmd="$cmd $model"
    
    echo "$cmd"
}

generate_commit_message() {
    log "Generating commit message with ${MODEL}..."
    
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
    
    # Create temp file for the complete prompt
    local temp_prompt_file
    temp_prompt_file="$(mktemp "/tmp/commit_prompt.XXXXXX")"
    
    log "Created temp prompt file: ${temp_prompt_file}"
    
    # Build the complete prompt with the template, files status, and diff
    {
        echo "$prompt_template"
        echo ""
        echo "FILES MODIFIED/ADDED:"
        echo "$files_status"
        echo ""
        echo "GIT DIFF:"
        echo "$git_diff"
    } > "$temp_prompt_file"
    
    log "Running command: ollama run $MODEL"
    log "Executing LLM with prompt..."
    
    # Try LLM with the complete prompt
    local response=""
    local llm_success=false
    
    # Build and execute ollama command
    local ollama_cmd_str
    ollama_cmd_str="$(build_ollama_command "$MODEL")"
    
    # Execute with error handling
    if response="$(cat "$temp_prompt_file" | $ollama_cmd_str 2>/dev/null)"; then
        llm_success=true
        log "LLM response received"
    else
        log "LLM execution failed, using fallback"
        llm_success=false
    fi
    
    # Clean up temp file
    rm -f "$temp_prompt_file"
    
    if [[ "$llm_success" == "true" && -n "$response" ]]; then
        # Extract the first line that looks like a conventional commit
        COMMIT_MESSAGE="$(echo "$response" | grep -E '^[a-z]+(\([^)]+\))?: .+' | head -n 1)"
        if [[ -z "$COMMIT_MESSAGE" ]]; then
            # If no conventional format found, take the first non-empty line
            COMMIT_MESSAGE="$(echo "$response" | grep -v '^[[:space:]]*$' | head -n 1)"
        fi
    else
        log "LLM did not respond or failed, using fallback"
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
    
    if [[ "$DRY_RUN" != "true" ]]; then
        echo "Staged changes summary:"
        git diff --cached --stat
        echo ""
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
    rm -f /tmp/commit_prompt.*
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

# Run main function
main "$@"

# Auto PR Desc

🤖 Automatic Pull Request description generator using local AI with Ollama.

## 📋 Description

Auto PR Desc is a tool that uses local AI models (via Ollama) to automatically generate structured and professional Pull Request descriptions. The tool analyzes changes in your current branch by comparing them with `origin/main` and generates a complete description following a standard template.

### ✨ Key Features

- 🚀 **Automatic generation**: Analyzes Git diffs and generates professional descriptions
- 🔍 **Optional validation**: Second AI model to review and improve quality
- 📁 **External prompts**: Separate configuration files for easy maintenance
- 🎯 **Standard template**: Follows consistent format for enterprise PRs
- ⚙️ **Configurable**: Environment variables and command line options
- 🌐 **Local**: Uses Ollama to keep everything on your machine

## 🛠️ Prerequisites

### Required Software

- **Git**: For change analysis and repository management
- **Ollama**: To run AI models locally
- **Bash**: Compatible shell (Linux/macOS/WSL)

### Ollama Models

Install the required models:

```bash
# Main model (recommended)
ollama pull llama3.1

# Validation model (optional)
ollama pull qwen2.5:7b
```

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/auto-pr-desc.git
   cd auto-pr-desc
   ```

2. **Make the script executable:**
   ```bash
   chmod +x gen-pr-desc.sh
   ```

3. **Optional - Add to PATH:**
   ```bash
   # Add to your ~/.bashrc or ~/.zshrc
   export PATH="$PATH:/path/to/auto-pr-desc"
   ```

## 🚀 Usage

### Basic Usage

```bash
# Generate basic description
./gen-pr-desc.sh

# Specify output file
./gen-pr-desc.sh my-pr-description.md

# Generate with validation
./gen-pr-desc.sh --validate
```

### Available Options

```bash
./gen-pr-desc.sh [OUTPUT_FILE] [--validate] [--help]
```

- `OUTPUT_FILE`: Output file name (default: `PR_DESCRIPTION.md`)
- `--validate`: Enables validation step with second model
- `--help, -h`: Shows complete help

### Environment Variables

```bash
# Main model
export MODEL="llama3.1"

# Validation model  
export VALIDATOR_MODEL="qwen2.5:7b"

# Diff lines limit
export MAX_DIFF_LINES=4000

# Context window size
export NUM_CTX=8192
```

## 📋 Workflow Example

1. **Make changes to your branch:**
   ```bash
   git checkout -b feature/new-functionality
   # ... make changes ...
   git add .
   git commit -m "Implement new functionality"
   ```

2. **Generate PR description:**
   ```bash
   ./gen-pr-desc.sh --validate
   ```

3. **Review and use the description:**
   ```bash
   cat PR_DESCRIPTION.md
   # Copy content to use in GitHub/GitLab
   ```

## 📁 Project Structure

```
auto-pr-desc/
├── gen-pr-desc.sh              # Enhanced main script
├── gen-pr-desc-original.sh     # Backup of original version
├── prompts/
│   ├── pr-generation.txt       # Prompt for main generation
│   └── pr-validation.txt       # Prompt for validation
└── README.md                   # Project documentation
```

## ⚙️ Advanced Configuration

### Customize Prompts

Files in `prompts/` can be modified to adapt the style and format of generated descriptions:

- **`pr-generation.txt`**: Controls how the initial description is generated
- **`pr-validation.txt`**: Defines how the description is validated and improved

### Alternative Models

You can use different Ollama models according to your needs:

```bash
# Lighter models
export MODEL="llama3.1:8b"
export VALIDATOR_MODEL="llama3.1:8b"

# More powerful models (require more RAM)
export MODEL="llama3.1:70b" 
export VALIDATOR_MODEL="llama3.1:70b"
```

## 🐛 Troubleshooting

### Error: "git is not installed"
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git
```

### Error: "ollama is not installed"
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### Error: "not inside a git repository"
```bash
# Initialize repository if needed
git init
git remote add origin <your-repository>
```

### Very large diff
If the diff is too extensive, adjust the limit:
```bash
export MAX_DIFF_LINES=8000
./gen-pr-desc.sh
```

## 🤝 Contributing

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is under the MIT License. See the `LICENSE` file for more details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for providing an easy way to run AI models locally
- Developer community that contributes to improving development tools

## 📞 Support

If you encounter any problems or have suggestions:

1. Check [existing Issues](../../issues)
2. Create a [New Issue](../../issues/new) with problem details
3. Include your system information and software versions

---

**Like the project? ⭐ Give it a star on GitHub!**

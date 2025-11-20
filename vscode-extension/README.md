# GitAI VS Code Extension

A VS Code extension that integrates with the GitAI CLI tool to provide AI-powered commit message and pull request description generation directly within VS Code.

## Features

- 🤖 **AI-Powered Commit Messages**: Generate commit messages based on staged changes
- 📝 **PR Description Generation**: Create detailed pull request descriptions
- 👁️ **Preview Mode**: Preview generated content before applying
- ⚙️ **Configurable**: Supports multiple AI providers (OpenAI, Anthropic, Ollama, LMStudio)
- 🎯 **Git Integration**: Seamlessly integrates with VS Code's built-in Git functionality
- 📊 **Status Bar**: Quick access and status indicators

## Prerequisites

1. **GitAI CLI**: This extension requires the GitAI CLI tool to be installed and available in your PATH.
   
   Install GitAI CLI:
   ```bash
   pip install gitai
   ```

2. **Git Repository**: You need to be working in a Git repository.

3. **AI Provider Setup**: Configure your AI provider (API keys, etc.) through GitAI CLI or VS Code settings.

## Installation

### From VSIX (Development)
1. Download the latest `.vsix` file
2. Open VS Code
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Type "Extensions: Install from VSIX"
5. Select the downloaded `.vsix` file

### From Marketplace (Coming Soon)
Search for "GitAI" in the VS Code Extensions marketplace.

## Usage

### Generate Commit Message

1. Stage your changes in VS Code's Source Control view
2. Use one of these methods:
   - Click the GitAI button in the Source Control toolbar
   - Open Command Palette (`Ctrl+Shift+P`) and run "GitAI: Generate Commit Message"
   - Click the GitAI status bar item (when changes are staged)

### Preview Commit Message

1. Stage your changes
2. Open Command Palette (`Ctrl+Shift+P`)
3. Run "GitAI: Preview Commit Message"
4. Review the generated message and choose to use it or generate a new one

### Generate PR Description

1. Open Command Palette (`Ctrl+Shift+P`)
2. Run "GitAI: Generate PR Description"
3. Enter the base branch (e.g., "main")
4. The generated description will open in a new document

### Configuration

#### Initialize GitAI Configuration

1. Open Command Palette (`Ctrl+Shift+P`)
2. Run "GitAI: Initialize GitAI Configuration"
3. This will create a `.gitai/config.yaml` file in your repository

#### VS Code Settings

Open VS Code settings and search for "GitAI" to configure:

- **Provider**: Choose your AI provider (openai, anthropic, ollama, lmstudio)
- **Model**: Specify the model name
- **API Key**: Set your API key (stored securely)
- **Template**: Choose the template for generated content
- **Auto Preview**: Enable/disable automatic preview
- **Max Tokens**: Set maximum tokens for generation

## Commands

| Command | Description |
|---------|-------------|
| `GitAI: Generate Commit Message` | Generate and apply commit message |
| `GitAI: Preview Commit Message` | Preview commit message before applying |
| `GitAI: Generate PR Description` | Generate pull request description |
| `GitAI: Open Configuration` | Open GitAI settings in VS Code |
| `GitAI: Initialize GitAI Configuration` | Create GitAI config file in repository |

## Configuration

The extension can be configured through VS Code settings or GitAI configuration files:

### VS Code Settings

```json
{
  "gitai.provider": "openai",
  "gitai.model": "gpt-4",
  "gitai.template": "conventional",
  "gitai.autoPreview": true,
  "gitai.maxTokens": 500
}
```

### GitAI Configuration Files

The extension respects GitAI's configuration hierarchy:
- Global: `~/.config/gitai/config.yaml`
- Team: `.gitai/config.yaml` (committed)
- Project: `.gitai-local/config.yaml` (git-ignored)

## Development

### Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   cd vscode-extension
   npm install
   ```

### Build

```bash
npm run compile
```

### Development Mode

1. Open the extension project in VS Code
2. Press `F5` to launch a new VS Code window with the extension loaded
3. Test the extension in the new window

### Package

```bash
npm run package
```

This creates a `.vsix` file that can be installed manually.

## Troubleshooting

### GitAI CLI Not Found

If you see "GitAI CLI not found" error:

1. Ensure GitAI is installed: `pip install gitai`
2. Verify it's in your PATH: `gitai --version`
3. If using a virtual environment, ensure it's activated when starting VS Code
4. Check the GitAI CLI path in VS Code settings

### No Staged Changes

The extension requires staged changes to generate commit messages:

1. Make some changes to your files
2. Stage them using VS Code's Source Control view or `git add`
3. Then run the commit message generation

### API Key Issues

If you're having API key problems:

1. Check your VS Code settings for the API key
2. Verify the API key in your GitAI configuration files
3. Ensure the correct provider is selected
4. Check the GitAI output channel for detailed error messages

## Support

- **Issues**: Report bugs and feature requests on [GitHub](https://github.com/gitai/gitai/issues)
- **Documentation**: Full GitAI documentation at [docs.gitai.dev](https://docs.gitai.dev)
- **Logs**: Check the "GitAI" output channel in VS Code for detailed logs

## License

MIT - See [LICENSE](../LICENSE) for details.
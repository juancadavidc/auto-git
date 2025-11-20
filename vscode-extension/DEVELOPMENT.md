# GitAI VS Code Extension - Development Guide

This guide covers development setup, testing, and packaging for the GitAI VS Code extension.

## Project Structure

```
vscode-extension/
├── package.json              # Extension manifest and dependencies
├── tsconfig.json            # TypeScript configuration
├── .eslintrc.json           # ESLint configuration
├── src/
│   ├── extension.ts         # Main extension entry point
│   ├── commands/            # Command implementations
│   │   └── gitaiCommands.ts # GitAI command handlers
│   ├── providers/           # Service providers
│   │   └── gitaiProvider.ts # GitAI CLI integration
│   └── utils/               # Utility modules
│       ├── logger.ts        # Logging utilities
│       └── statusBar.ts     # Status bar integration
├── media/                   # Icons and assets
├── out/                     # Compiled JavaScript (generated)
└── README.md               # User documentation
```

## Development Setup

### Prerequisites

1. **Node.js** (v16 or higher)
2. **VS Code** (latest version)
3. **GitAI CLI** installed and in PATH
4. **Git** repository for testing

### Installation

1. Navigate to the extension directory:
   ```bash
   cd vscode-extension
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Install the VS Code Extension Manager (if not already installed):
   ```bash
   npm install -g @vscode/vsce
   ```

## Development Workflow

### 1. Compile TypeScript

Compile once:
```bash
npm run compile
```

Watch mode (auto-compile on changes):
```bash
npm run watch
```

### 2. Run Extension in Development

1. Open the extension project in VS Code
2. Press `F5` to launch Extension Development Host
3. This opens a new VS Code window with the extension loaded
4. Test the extension features in the new window

### 3. Testing

#### Manual Testing Checklist

1. **Installation Check**:
   - [ ] Extension loads without errors
   - [ ] GitAI CLI detection works
   - [ ] Status bar appears

2. **Commit Message Generation**:
   - [ ] Stage some changes
   - [ ] Run "Generate Commit Message" command
   - [ ] Verify message appears in commit input
   - [ ] Test with no staged changes (should show warning)

3. **Preview Functionality**:
   - [ ] Run "Preview Commit Message" command
   - [ ] Verify preview dialog appears
   - [ ] Test "Use This Message" option
   - [ ] Test "Generate New" option

4. **PR Description**:
   - [ ] Run "Generate PR Description" command
   - [ ] Enter base branch
   - [ ] Verify description opens in new document

5. **Configuration**:
   - [ ] Run "Initialize GitAI Configuration"
   - [ ] Verify config file creation
   - [ ] Test "Open Configuration" command
   - [ ] Modify VS Code settings and verify they're passed to CLI

6. **Status Bar**:
   - [ ] Verify status shows correctly with/without repo
   - [ ] Verify status changes with staged/unstaged changes
   - [ ] Test clicking status bar item

#### Error Scenarios

- [ ] No git repository
- [ ] GitAI CLI not installed
- [ ] Invalid API key
- [ ] Network issues
- [ ] Empty repository
- [ ] Large repositories

### 4. Linting

Run ESLint:
```bash
npm run lint
```

Fix auto-fixable issues:
```bash
npm run lint -- --fix
```

### 5. Debugging

#### VS Code Debugger

1. Set breakpoints in TypeScript files
2. Press `F5` to start debugging
3. Interact with the extension in the Extension Development Host
4. Debugger will pause at breakpoints

#### Logging

Use the Logger utility for debugging:

```typescript
import { Logger } from '../utils/logger';

Logger.info('Debug message', { data: 'value' });
Logger.error('Error message', error);
```

View logs in:
- VS Code Output panel → "GitAI" channel
- Browser console (F12)

## Building and Packaging

### 1. Compile for Production

```bash
npm run vscode:prepublish
```

### 2. Package Extension

Create a `.vsix` file:

```bash
npm run package
```

This creates `gitai-vscode-0.1.0.vsix` (or similar) that can be installed manually.

### 3. Install Packaged Extension

```bash
code --install-extension gitai-vscode-0.1.0.vsix
```

## Extension Architecture

### Main Components

1. **Extension Entry Point** (`extension.ts`):
   - Activates when VS Code starts
   - Registers commands and providers
   - Initializes status bar

2. **GitAI Commands** (`commands/gitaiCommands.ts`):
   - Implements command handlers
   - Manages user interactions
   - Handles progress and error reporting

3. **GitAI Provider** (`providers/gitaiProvider.ts`):
   - Executes GitAI CLI commands
   - Manages configuration
   - Handles CLI output parsing

4. **Status Bar** (`utils/statusBar.ts`):
   - Shows GitAI status
   - Provides quick access to commands
   - Responds to git repository changes

5. **Logger** (`utils/logger.ts`):
   - Centralized logging
   - Output channel integration
   - Debug information

### VS Code API Integration

The extension integrates with:

- **Commands API**: Register and execute commands
- **Git Extension API**: Access git repository state
- **Configuration API**: Read/write settings
- **Window API**: Show notifications and progress
- **Workspace API**: Access workspace folders

### GitAI CLI Integration

The extension communicates with GitAI CLI through:

1. **Process Spawning**: Uses `child_process.spawn()`
2. **Environment Variables**: Passes VS Code settings as env vars
3. **Output Parsing**: Processes CLI stdout/stderr
4. **Error Handling**: Manages CLI errors and timeouts

## Configuration Management

### VS Code Settings

Settings are defined in `package.json` under `contributes.configuration`:

```json
{
  "gitai.provider": {
    "type": "string",
    "enum": ["openai", "anthropic", "ollama", "lmstudio"],
    "default": "openai"
  }
}
```

### Runtime Configuration

Settings are passed to GitAI CLI as environment variables:

```typescript
env: {
  GITAI_PROVIDER: vscode.workspace.getConfiguration('gitai').get('provider'),
  GITAI_API_KEY: vscode.workspace.getConfiguration('gitai').get('apiKey'),
  // ...
}
```

## Publishing

### Marketplace Publishing

1. Get a Personal Access Token from Azure DevOps
2. Login to vsce:
   ```bash
   vsce login <publisher>
   ```
3. Publish:
   ```bash
   vsce publish
   ```

### Manual Distribution

Share the `.vsix` file directly:
1. Build the package: `npm run package`
2. Share `gitai-vscode-x.x.x.vsix`
3. Install with: `code --install-extension gitai-vscode-x.x.x.vsix`

## Common Issues

### TypeScript Compilation Errors

- Check `tsconfig.json` configuration
- Ensure all imports are correct
- Verify VS Code API types are up to date

### Extension Not Loading

- Check `package.json` manifest
- Verify activation events
- Look for errors in Developer Console (`Help` → `Toggle Developer Tools`)

### GitAI CLI Integration Issues

- Verify CLI installation: `gitai --version`
- Check PATH environment variable
- Test CLI commands manually
- Review GitAI logs in output channel

## Best Practices

1. **Error Handling**: Always wrap CLI calls in try-catch
2. **User Feedback**: Show progress for long operations
3. **Configuration**: Validate settings before use
4. **Logging**: Log important operations and errors
5. **Performance**: Use async/await for non-blocking operations
6. **Security**: Don't log sensitive information (API keys)

## Contributing

1. Follow the existing code style
2. Add appropriate error handling
3. Update tests for new features
4. Update documentation
5. Test thoroughly before submitting PRs
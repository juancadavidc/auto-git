import * as vscode from 'vscode';
import { GitAICommands } from './commands/gitaiCommands';
import { GitAIProvider } from './providers/gitaiProvider';
import { GitAIStatusBar } from './utils/statusBar';
import { Logger } from './utils/logger';

let gitaiCommands: GitAICommands;
let gitaiProvider: GitAIProvider;
let statusBar: GitAIStatusBar;

export function activate(context: vscode.ExtensionContext) {
    Logger.info('GitAI extension is being activated');

    // Initialize components
    gitaiProvider = new GitAIProvider(context);
    gitaiCommands = new GitAICommands(context, gitaiProvider);
    statusBar = new GitAIStatusBar(context);

    // Register commands
    registerCommands(context);

    // Check if GitAI CLI is available
    checkGitAIAvailability();

    Logger.info('GitAI extension activated successfully');
}

export function deactivate() {
    Logger.info('GitAI extension is being deactivated');
    
    if (statusBar) {
        statusBar.dispose();
    }
    
    Logger.info('GitAI extension deactivated');
}

function registerCommands(context: vscode.ExtensionContext) {
    const commands = [
        vscode.commands.registerCommand('gitai.generateCommitMessage', () => {
            gitaiCommands.generateCommitMessage();
        }),
        
        vscode.commands.registerCommand('gitai.generatePRDescription', () => {
            gitaiCommands.generatePRDescription();
        }),
        
        vscode.commands.registerCommand('gitai.previewCommit', () => {
            gitaiCommands.previewCommitMessage();
        }),
        
        vscode.commands.registerCommand('gitai.openConfig', () => {
            gitaiCommands.openConfiguration();
        }),
        
        vscode.commands.registerCommand('gitai.initConfig', () => {
            gitaiCommands.initializeConfiguration();
        })
    ];

    commands.forEach(command => context.subscriptions.push(command));
    
    Logger.info(`Registered ${commands.length} GitAI commands`);
}

async function checkGitAIAvailability() {
    try {
        const isAvailable = await gitaiProvider.checkGitAIInstallation();
        if (!isAvailable) {
            vscode.window.showWarningMessage(
                'GitAI CLI not found. Please install GitAI to use this extension.',
                'Install GitAI',
                'Learn More'
            ).then(selection => {
                if (selection === 'Install GitAI') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/gitai/gitai#installation'));
                } else if (selection === 'Learn More') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/gitai/gitai'));
                }
            });
        } else {
            statusBar.updateStatus('GitAI Ready', 'GitAI is ready to use');
            Logger.info('GitAI CLI is available and ready');
        }
    } catch (error) {
        Logger.error('Failed to check GitAI availability:', error);
        statusBar.updateStatus('GitAI Error', 'Failed to check GitAI installation');
    }
}
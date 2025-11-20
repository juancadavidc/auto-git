import * as vscode from 'vscode';
import { GitAIProvider } from '../providers/gitaiProvider';
import { Logger } from '../utils/logger';

export class GitAICommands {
    constructor(
        private context: vscode.ExtensionContext,
        private gitaiProvider: GitAIProvider
    ) {}

    async generateCommitMessage(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
            const git = gitExtension?.getAPI(1);
            
            if (!git || git.repositories.length === 0) {
                vscode.window.showErrorMessage('No git repository found');
                return;
            }

            const repo = git.repositories[0];
            
            // Check if there are staged changes
            if (repo.state.indexChanges.length === 0) {
                vscode.window.showWarningMessage('No staged changes found. Stage some changes first.');
                return;
            }

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Generating commit message...',
                cancellable: true
            }, async (progress, token) => {
                try {
                    const commitMessage = await this.gitaiProvider.generateCommitMessage(workspaceFolder.uri.fsPath);
                    
                    if (token.isCancellationRequested) {
                        return;
                    }

                    if (commitMessage) {
                        // Set the commit message in the Source Control input box
                        repo.inputBox.value = commitMessage;
                        vscode.window.showInformationMessage('Commit message generated successfully!');
                    } else {
                        vscode.window.showWarningMessage('No commit message was generated');
                    }
                } catch (error) {
                    Logger.error('Failed to generate commit message:', error);
                    vscode.window.showErrorMessage(`Failed to generate commit message: ${error}`);
                }
            });
        } catch (error) {
            Logger.error('Error in generateCommitMessage:', error);
            vscode.window.showErrorMessage(`Error generating commit message: ${error}`);
        }
    }

    async previewCommitMessage(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Generating commit message preview...',
                cancellable: true
            }, async (progress, token) => {
                try {
                    const preview = await this.gitaiProvider.previewCommitMessage(workspaceFolder.uri.fsPath);
                    
                    if (token.isCancellationRequested) {
                        return;
                    }

                    if (preview) {
                        const action = await vscode.window.showInformationMessage(
                            'Commit message preview generated',
                            { modal: true, detail: preview },
                            'Use This Message',
                            'Generate New',
                            'Cancel'
                        );

                        if (action === 'Use This Message') {
                            const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
                            const git = gitExtension?.getAPI(1);
                            if (git && git.repositories.length > 0) {
                                git.repositories[0].inputBox.value = preview;
                            }
                        } else if (action === 'Generate New') {
                            this.previewCommitMessage();
                        }
                    }
                } catch (error) {
                    Logger.error('Failed to preview commit message:', error);
                    vscode.window.showErrorMessage(`Failed to preview commit message: ${error}`);
                }
            });
        } catch (error) {
            Logger.error('Error in previewCommitMessage:', error);
            vscode.window.showErrorMessage(`Error previewing commit message: ${error}`);
        }
    }

    async generatePRDescription(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            // Get base branch for PR
            const baseBranch = await vscode.window.showInputBox({
                prompt: 'Enter the base branch for the PR',
                value: 'main',
                placeHolder: 'main'
            });

            if (!baseBranch) {
                return;
            }

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Generating PR description...',
                cancellable: true
            }, async (progress, token) => {
                try {
                    const prDescription = await this.gitaiProvider.generatePRDescription(workspaceFolder.uri.fsPath, baseBranch);
                    
                    if (token.isCancellationRequested) {
                        return;
                    }

                    if (prDescription) {
                        // Open a new untitled document with the PR description
                        const doc = await vscode.workspace.openTextDocument({
                            content: prDescription,
                            language: 'markdown'
                        });
                        await vscode.window.showTextDocument(doc);
                        vscode.window.showInformationMessage('PR description generated successfully!');
                    }
                } catch (error) {
                    Logger.error('Failed to generate PR description:', error);
                    vscode.window.showErrorMessage(`Failed to generate PR description: ${error}`);
                }
            });
        } catch (error) {
            Logger.error('Error in generatePRDescription:', error);
            vscode.window.showErrorMessage(`Error generating PR description: ${error}`);
        }
    }

    async openConfiguration(): Promise<void> {
        try {
            // Open VS Code settings for GitAI
            await vscode.commands.executeCommand('workbench.action.openSettings', 'gitai');
        } catch (error) {
            Logger.error('Error opening configuration:', error);
            vscode.window.showErrorMessage('Failed to open configuration');
        }
    }

    async initializeConfiguration(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Initializing GitAI configuration...',
                cancellable: false
            }, async () => {
                try {
                    const success = await this.gitaiProvider.initializeConfig(workspaceFolder.uri.fsPath);
                    
                    if (success) {
                        vscode.window.showInformationMessage('GitAI configuration initialized successfully!');
                    } else {
                        vscode.window.showWarningMessage('GitAI configuration may already exist or initialization failed');
                    }
                } catch (error) {
                    Logger.error('Failed to initialize configuration:', error);
                    vscode.window.showErrorMessage(`Failed to initialize configuration: ${error}`);
                }
            });
        } catch (error) {
            Logger.error('Error in initializeConfiguration:', error);
            vscode.window.showErrorMessage(`Error initializing configuration: ${error}`);
        }
    }
}
import * as vscode from 'vscode';
import * as cp from 'child_process';
import { Logger } from '../utils/logger';

export class GitAIProvider {
    private gitaiPath: string;

    constructor(private context: vscode.ExtensionContext) {
        // Get GitAI CLI path from configuration or use default
        const config = vscode.workspace.getConfiguration('gitai');
        this.gitaiPath = config.get('cliPath', 'gitai');
    }

    async checkGitAIInstallation(): Promise<boolean> {
        try {
            const result = await this.executeGitAI(['--version'], '.');
            return result.success;
        } catch (error) {
            Logger.error('GitAI installation check failed:', error);
            return false;
        }
    }

    async generateCommitMessage(workingDirectory: string): Promise<string | null> {
        try {
            const result = await this.executeGitAI(['commit', '--preview'], workingDirectory);
            
            if (result.success && result.stdout) {
                // Parse the output to extract just the commit message
                const output = result.stdout.trim();
                // Remove any CLI formatting/headers and get the actual message
                const lines = output.split('\\n');
                const messageStartIndex = lines.findIndex(line => 
                    line.includes('Generated commit message:') || 
                    line.includes('Commit message:') ||
                    !line.startsWith('[') // Skip CLI log lines that start with [
                );
                
                if (messageStartIndex >= 0) {
                    return lines.slice(messageStartIndex + 1).join('\\n').trim();
                }
                
                return output;
            }
            
            throw new Error(result.stderr || 'Failed to generate commit message');
        } catch (error) {
            Logger.error('Failed to generate commit message:', error);
            throw error;
        }
    }

    async previewCommitMessage(workingDirectory: string): Promise<string | null> {
        try {
            const result = await this.executeGitAI(['commit', '--preview'], workingDirectory);
            
            if (result.success && result.stdout) {
                return result.stdout.trim();
            }
            
            throw new Error(result.stderr || 'Failed to preview commit message');
        } catch (error) {
            Logger.error('Failed to preview commit message:', error);
            throw error;
        }
    }

    async generatePRDescription(workingDirectory: string, baseBranch: string): Promise<string | null> {
        try {
            const result = await this.executeGitAI(['pr', '--base', baseBranch], workingDirectory);
            
            if (result.success && result.stdout) {
                return result.stdout.trim();
            }
            
            throw new Error(result.stderr || 'Failed to generate PR description');
        } catch (error) {
            Logger.error('Failed to generate PR description:', error);
            throw error;
        }
    }

    async initializeConfig(workingDirectory: string): Promise<boolean> {
        try {
            const result = await this.executeGitAI(['config', 'init'], workingDirectory);
            return result.success;
        } catch (error) {
            Logger.error('Failed to initialize config:', error);
            return false;
        }
    }

    private async executeGitAI(args: string[], workingDirectory: string): Promise<{
        success: boolean;
        stdout: string;
        stderr: string;
    }> {
        return new Promise((resolve) => {
            const childProcess = cp.spawn(this.gitaiPath, args, {
                cwd: workingDirectory,
                env: {
                    ...process.env,
                    // Pass VS Code configuration as environment variables
                    GITAI_PROVIDER: vscode.workspace.getConfiguration('gitai').get('provider', 'openai'),
                    GITAI_MODEL: vscode.workspace.getConfiguration('gitai').get('model', 'gpt-4'),
                    GITAI_API_KEY: vscode.workspace.getConfiguration('gitai').get('apiKey', ''),
                    GITAI_TEMPLATE: vscode.workspace.getConfiguration('gitai').get('template', 'conventional'),
                    GITAI_MAX_TOKENS: vscode.workspace.getConfiguration('gitai').get('maxTokens', '500').toString(),
                }
            });

            let stdout = '';
            let stderr = '';

            childProcess.stdout.on('data', (data: Buffer) => {
                stdout += data.toString();
            });

            childProcess.stderr.on('data', (data: Buffer) => {
                stderr += data.toString();
            });

            childProcess.on('close', (code: number | null) => {
                resolve({
                    success: code === 0,
                    stdout,
                    stderr
                });
            });

            childProcess.on('error', (error: Error) => {
                Logger.error('GitAI process error:', error);
                resolve({
                    success: false,
                    stdout: '',
                    stderr: error.message
                });
            });

            // Set a timeout for the process
            setTimeout(() => {
                if (!childProcess.killed) {
                    childProcess.kill();
                    resolve({
                        success: false,
                        stdout: '',
                        stderr: 'GitAI command timed out'
                    });
                }
            }, 30000); // 30 second timeout
        });
    }
}
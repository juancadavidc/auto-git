import * as vscode from 'vscode';

export class GitAIStatusBar {
    private statusBarItem: vscode.StatusBarItem;

    constructor(private context: vscode.ExtensionContext) {
        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left, 
            100
        );
        
        // Set default properties
        this.statusBarItem.command = 'gitai.generateCommitMessage';
        this.statusBarItem.text = '$(robot) GitAI';
        this.statusBarItem.tooltip = 'Click to generate commit message';
        
        // Show the status bar item
        this.statusBarItem.show();
        
        // Add to subscriptions for cleanup
        context.subscriptions.push(this.statusBarItem);
        
        // Listen for git repository changes
        this.setupGitListener();
    }

    updateStatus(text: string, tooltip?: string) {
        this.statusBarItem.text = `$(robot) ${text}`;
        if (tooltip) {
            this.statusBarItem.tooltip = tooltip;
        }
    }

    updateForRepository(hasRepo: boolean, hasChanges: boolean = false) {
        if (!hasRepo) {
            this.statusBarItem.text = '$(robot) GitAI';
            this.statusBarItem.tooltip = 'No git repository found';
            this.statusBarItem.command = undefined;
            this.statusBarItem.color = undefined;
        } else if (hasChanges) {
            this.statusBarItem.text = '$(robot) GitAI';
            this.statusBarItem.tooltip = 'Click to generate commit message';
            this.statusBarItem.command = 'gitai.generateCommitMessage';
            this.statusBarItem.color = new vscode.ThemeColor('statusBarItem.prominentForeground');
        } else {
            this.statusBarItem.text = '$(robot) GitAI';
            this.statusBarItem.tooltip = 'No staged changes';
            this.statusBarItem.command = 'gitai.generateCommitMessage';
            this.statusBarItem.color = undefined;
        }
    }

    private setupGitListener() {
        // Listen for git extension availability
        const gitExtension = vscode.extensions.getExtension('vscode.git');
        if (gitExtension) {
            if (gitExtension.isActive) {
                this.setupGitRepositoryListener(gitExtension.exports);
            } else {
                gitExtension.activate().then(() => {
                    this.setupGitRepositoryListener(gitExtension.exports);
                });
            }
        }
    }

    private setupGitRepositoryListener(gitApi: any) {
        try {
            const git = gitApi.getAPI(1);
            
            // Initial state
            this.updateRepositoryState(git);
            
            // Listen for repository changes
            git.onDidOpenRepository(() => {
                this.updateRepositoryState(git);
            });
            
            git.onDidCloseRepository(() => {
                this.updateRepositoryState(git);
            });
            
            // Listen for changes in repositories
            git.repositories.forEach((repo: any) => {
                repo.state.onDidChange(() => {
                    this.updateRepositoryState(git);
                });
            });
            
        } catch (error) {
            console.error('Failed to setup git repository listener:', error);
        }
    }

    private updateRepositoryState(git: any) {
        const hasRepo = git.repositories.length > 0;
        let hasChanges = false;
        
        if (hasRepo) {
            // Check if any repository has staged changes
            hasChanges = git.repositories.some((repo: any) => 
                repo.state.indexChanges.length > 0
            );
        }
        
        this.updateForRepository(hasRepo, hasChanges);
    }

    dispose() {
        this.statusBarItem.dispose();
    }
}
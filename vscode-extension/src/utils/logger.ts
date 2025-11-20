import * as vscode from 'vscode';

export class Logger {
    private static outputChannel: vscode.OutputChannel;

    static initialize() {
        if (!Logger.outputChannel) {
            Logger.outputChannel = vscode.window.createOutputChannel('GitAI');
        }
    }

    static info(message: string, ...args: any[]) {
        Logger.initialize();
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] INFO: ${message}`;
        Logger.outputChannel.appendLine(formattedMessage);
        
        if (args.length > 0) {
            Logger.outputChannel.appendLine(JSON.stringify(args, null, 2));
        }
        
        console.log(formattedMessage, ...args);
    }

    static error(message: string, error?: any) {
        Logger.initialize();
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] ERROR: ${message}`;
        Logger.outputChannel.appendLine(formattedMessage);
        
        if (error) {
            const errorDetails = error instanceof Error 
                ? `${error.message}\\n${error.stack}` 
                : JSON.stringify(error, null, 2);
            Logger.outputChannel.appendLine(errorDetails);
        }
        
        console.error(formattedMessage, error);
    }

    static warn(message: string, ...args: any[]) {
        Logger.initialize();
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] WARN: ${message}`;
        Logger.outputChannel.appendLine(formattedMessage);
        
        if (args.length > 0) {
            Logger.outputChannel.appendLine(JSON.stringify(args, null, 2));
        }
        
        console.warn(formattedMessage, ...args);
    }

    static debug(message: string, ...args: any[]) {
        Logger.initialize();
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] DEBUG: ${message}`;
        Logger.outputChannel.appendLine(formattedMessage);
        
        if (args.length > 0) {
            Logger.outputChannel.appendLine(JSON.stringify(args, null, 2));
        }
        
        console.debug(formattedMessage, ...args);
    }

    static show() {
        Logger.initialize();
        Logger.outputChannel.show();
    }

    static dispose() {
        if (Logger.outputChannel) {
            Logger.outputChannel.dispose();
        }
    }
}
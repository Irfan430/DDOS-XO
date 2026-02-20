import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Terminal, Play, Trash2 } from "lucide-react";

interface SystemExecutorProps {
  onExecute?: (command: string) => Promise<string>;
}

export default function SystemExecutor({ onExecute }: SystemExecutorProps) {
  const [command, setCommand] = useState("");
  const [output, setOutput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [requiresPermission, setRequiresPermission] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState(false);

  const handleExecute = async () => {
    if (!command.trim()) return;

    if (requiresPermission && !permissionGranted) {
      setError("Permission required to execute this command");
      return;
    }

    setIsExecuting(true);
    setError("");
    setOutput("");

    try {
      if (onExecute) {
        const result = await onExecute(command);
        setOutput(result);
      } else {
        // Simulate execution
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setOutput(`$ ${command}\n\nCommand executed successfully.\n\nOutput would appear here.`);
      }
      setHistory([...history, command]);
      setCommand("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClear = () => {
    setCommand("");
    setOutput("");
    setError("");
  };

  const handleHistorySelect = (cmd: string) => {
    setCommand(cmd);
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Command Input */}
      <Card className="p-4 space-y-3">
        <div className="space-y-2">
          <label className="text-sm font-medium">System Command</label>
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-muted-foreground" />
            <Input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleExecute()}
              placeholder="Enter command (e.g., ls, pwd, git status)..."
              disabled={isExecuting}
              className="flex-1 font-mono"
            />
          </div>
        </div>

        {/* Permission Control */}
        <div className="flex items-center gap-2 p-2 bg-card/50 rounded">
          <Checkbox
            id="requires-permission"
            checked={requiresPermission}
            onCheckedChange={(checked) => {
              setRequiresPermission(checked as boolean);
              setPermissionGranted(false);
            }}
          />
          <label htmlFor="requires-permission" className="text-sm cursor-pointer flex-1">
            This command requires elevated permissions
          </label>
        </div>

        {requiresPermission && !permissionGranted && (
          <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
            ⚠️ Grant permission to execute this command
            <Button
              onClick={() => setPermissionGranted(true)}
              variant="outline"
              size="sm"
              className="ml-2 h-6"
            >
              Grant Permission
            </Button>
          </div>
        )}

        {/* Control Buttons */}
        <div className="flex items-center gap-2">
          <Button
            onClick={handleExecute}
            disabled={isExecuting || !command.trim()}
            className="gap-2"
          >
            {isExecuting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Execute
          </Button>

          <Button
            onClick={handleClear}
            variant="outline"
            size="icon"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </Card>

      {/* Output and History */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Output Panel */}
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-sm font-medium">Output</label>
          <Card className="flex-1 p-4 bg-card/50 overflow-hidden flex flex-col font-mono text-sm">
            {error ? (
              <div className="text-red-400 whitespace-pre-wrap break-words">
                {error}
              </div>
            ) : (
              <ScrollArea className="flex-1">
                <div className="text-muted-foreground whitespace-pre-wrap break-words">
                  {output || "Output will appear here..."}
                </div>
              </ScrollArea>
            )}
          </Card>
        </div>

        {/* History Panel */}
        {history.length > 0 && (
          <div className="w-64 flex flex-col gap-2">
            <label className="text-sm font-medium">Command History</label>
            <Card className="flex-1 p-3 overflow-hidden flex flex-col">
              <ScrollArea className="flex-1">
                <div className="space-y-1">
                  {history.map((cmd, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleHistorySelect(cmd)}
                      className="w-full text-left px-2 py-1 text-xs font-mono bg-card/50 hover:bg-card rounded border border-border hover:border-accent transition-colors truncate"
                      title={cmd}
                    >
                      {cmd}
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

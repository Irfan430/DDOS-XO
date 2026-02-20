import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Play, Copy, Trash2 } from "lucide-react";

interface CodeExecutorProps {
  onExecute?: (code: string, language: string) => Promise<string>;
}

export default function CodeExecutor({ onExecute }: CodeExecutorProps) {
  const [code, setCode] = useState("# Write your code here\nprint('Hello, World!')");
  const [language, setLanguage] = useState("python");
  const [output, setOutput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState("");

  const handleExecute = async () => {
    setIsExecuting(true);
    setError("");
    setOutput("");

    try {
      if (onExecute) {
        const result = await onExecute(code, language);
        setOutput(result);
      } else {
        setOutput(`Executing ${language} code...`);
        const result = await fetch('/api/trpc/code.execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, language }),
        });
        const data = await result.json();
        setOutput(data.result?.output || `${language} code executed successfully`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
  };

  const handleClear = () => {
    setCode("");
    setOutput("");
    setError("");
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Language Selection and Controls */}
      <div className="flex items-center gap-2">
        <Select value={language} onValueChange={setLanguage}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="python">Python</SelectItem>
            <SelectItem value="javascript">JavaScript</SelectItem>
            <SelectItem value="bash">Bash</SelectItem>
            <SelectItem value="sql">SQL</SelectItem>
            <SelectItem value="json">JSON</SelectItem>
          </SelectContent>
        </Select>

        <Button
          onClick={handleExecute}
          disabled={isExecuting || !code.trim()}
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
          onClick={handleCopy}
          variant="outline"
          size="icon"
          title="Copy code"
        >
          <Copy className="w-4 h-4" />
        </Button>

        <Button
          onClick={handleClear}
          variant="outline"
          size="icon"
          title="Clear"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Code Editor */}
      <div className="flex-1 flex gap-4 min-h-0">
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-sm font-medium">Code</label>
          <Textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Write your code here..."
            className="flex-1 font-mono text-sm resize-none"
          />
        </div>

        {/* Output Panel */}
        <div className="flex-1 flex flex-col gap-2">
          <label className="text-sm font-medium">Output</label>
          <Card className="flex-1 p-4 bg-card/50 overflow-hidden flex flex-col">
            {error ? (
              <div className="text-red-400 text-sm font-mono whitespace-pre-wrap break-words">
                {error}
              </div>
            ) : (
              <ScrollArea className="flex-1">
                <div className="text-sm font-mono text-muted-foreground whitespace-pre-wrap break-words">
                  {output || "Output will appear here..."}
                </div>
              </ScrollArea>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

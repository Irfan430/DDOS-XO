import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, GitBranch, GitCommit, Upload } from "lucide-react";

interface GitHubPanelProps {
  onPush?: (repo: string, message: string, files: string[]) => Promise<void>;
}

export default function GitHubPanel({ onPush }: GitHubPanelProps) {
  const [repo, setRepo] = useState("Irfan430/DDOS-XO");
  const [branch, setBranch] = useState("main");
  const [commitMessage, setCommitMessage] = useState("");
  const [files, setFiles] = useState<string[]>([]);
  const [isPushing, setIsPushing] = useState(false);
  const [commits, setCommits] = useState<Array<{
    id: string;
    message: string;
    author: string;
    date: string;
  }>>([
    {
      id: "abc123",
      message: "Initial commit: Setup agent interface",
      author: "Agent",
      date: new Date().toISOString(),
    },
  ]);

  const handlePush = async () => {
    if (!commitMessage.trim() || files.length === 0) return;

    setIsPushing(true);
    try {
      if (onPush) {
        await onPush(repo, commitMessage, files);
      } else {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        setCommits((prev) => [
          {
            id: Math.random().toString(36).substr(2, 9),
            message: commitMessage,
            author: "Agent",
            date: new Date().toISOString(),
          },
          ...prev,
        ]);
      }
      setCommitMessage("");
      setFiles([]);
    } finally {
      setIsPushing(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      <Tabs defaultValue="push" className="flex-1 flex flex-col">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="push" className="gap-2">
            <Upload className="w-4 h-4" /> Push Code
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <GitCommit className="w-4 h-4" /> Commit History
          </TabsTrigger>
        </TabsList>

        {/* Push Tab */}
        <TabsContent value="push" className="flex-1 flex flex-col gap-4">
          <Card className="p-4 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Repository</label>
              <Input
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="owner/repo"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Branch</label>
                <Input
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Commit Message</label>
              <Textarea
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                placeholder="Describe your changes..."
                className="resize-none h-24"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Files to Push</label>
              <div className="border border-border rounded-lg p-3 space-y-2 max-h-32 overflow-y-auto">
                {files.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No files selected</p>
                ) : (
                  files.map((file) => (
                    <div
                      key={file}
                      className="flex items-center justify-between text-sm p-2 bg-card rounded"
                    >
                      <span>{file}</span>
                      <button
                        onClick={() => setFiles(files.filter((f) => f !== file))}
                        className="text-xs text-red-400 hover:text-red-300"
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>
              <Input
                type="text"
                placeholder="Add file path (e.g., src/App.tsx)"
                onKeyPress={(e) => {
                  if (e.key === "Enter" && e.currentTarget.value) {
                    setFiles([...files, e.currentTarget.value]);
                    e.currentTarget.value = "";
                  }
                }}
              />
            </div>

            <Button
              onClick={handlePush}
              disabled={isPushing || !commitMessage.trim() || files.length === 0}
              className="w-full gap-2"
            >
              {isPushing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              Push to GitHub
            </Button>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="flex-1 flex flex-col">
          <ScrollArea className="flex-1">
            <div className="space-y-3 p-4">
              {commits.map((commit) => (
                <Card key={commit.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                      <GitCommit className="w-4 h-4 text-accent" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm break-words">{commit.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {commit.author} · {new Date(commit.date).toLocaleString()}
                      </p>
                      <p className="text-xs font-mono text-muted-foreground mt-1">
                        {commit.id}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

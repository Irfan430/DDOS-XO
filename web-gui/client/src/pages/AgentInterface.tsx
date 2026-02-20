import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Mic, Send, Settings, Github, Code, Globe, Terminal, Activity } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import CodeExecutor from "@/components/CodeExecutor";
import GitHubPanel from "@/components/GitHubPanel";
import BrowserAutomation from "@/components/BrowserAutomation";
import SystemExecutor from "@/components/SystemExecutor";
import SettingsPanel from "@/components/SettingsPanel";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ActivityEntry {
  id: string;
  agentName: string;
  taskName: string;
  status: "pending" | "executing" | "success" | "failed" | "partial";
  confidence: number;
  riskLevel: "LOW" | "MEDIUM" | "HIGH";
  timestamp: Date;
}

export default function AgentInterface() {
  const { user, loading: authLoading } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [cpuUsage, setCpuUsage] = useState(0);
  const [ramUsage, setRamUsage] = useState(0);
  const [thoughtProcess, setThoughtProcess] = useState("");
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Fetch messages
  const { data: fetchedMessages } = trpc.chat.getMessages.useQuery(undefined, {
    enabled: !!user,
  });

  // Fetch activities
  const { data: fetchedActivities } = trpc.activity.getLogs.useQuery(undefined, {
    enabled: !!user,
  });

  // Send message mutation
  const sendMessageMutation = trpc.chat.sendMessage.useMutation();

  useEffect(() => {
    if (fetchedMessages) {
      setMessages(
        fetchedMessages.map((msg) => ({
          id: msg.id.toString(),
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
        }))
      );
    }
  }, [fetchedMessages]);

  useEffect(() => {
    if (fetchedActivities) {
      setActivities(
        fetchedActivities.map((activity) => ({
          id: activity.id.toString(),
          agentName: activity.agentName,
          taskName: activity.taskName,
          status: activity.status,
          confidence: activity.confidence || 0,
          riskLevel: (activity.riskLevel || "LOW") as "LOW" | "MEDIUM" | "HIGH",
          timestamp: new Date(activity.timestamp),
        }))
      );
    }
  }, [fetchedActivities]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onstart = () => {
        setIsListening(true);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onresult = (event: any) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        if (event.results[event.results.length - 1].isFinal) {
          setInputValue(transcript);
        }
      };
    }
  }, []);

  // Simulate system resource monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      setCpuUsage(Math.random() * 100);
      setRamUsage(Math.random() * 100);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsSending(true);
    setThoughtProcess("🧠 Agent is thinking...");

    try {
      const result = await sendMessageMutation.mutateAsync({ content: inputValue });
      
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.response || "I've processed your request.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentMessage]);
      setThoughtProcess("");
    } catch (error) {
      console.error("Failed to send message:", error);
      setThoughtProcess("❌ Error processing message");
    } finally {
      setIsSending(false);
    }
  };

  const toggleVoiceInput = () => {
    if (recognitionRef.current) {
      if (isListening) {
        recognitionRef.current.stop();
      } else {
        recognitionRef.current.start();
      }
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Header with System Monitoring */}
      <div className="border-b border-border bg-card p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
              <span className="text-accent font-bold">🤖</span>
            </div>
            <div>
              <h1 className="text-xl font-bold">DDOS-XO Agent Interface</h1>
              <p className="text-sm text-muted-foreground">AI-Powered Autonomous Control System</p>
            </div>
          </div>
          
          {/* System Monitoring */}
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-xs text-muted-foreground">CPU Usage</span>
              <div className="w-24 h-2 bg-card rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all"
                  style={{ width: `${cpuUsage}%` }}
                />
              </div>
              <span className="text-xs font-mono">{cpuUsage.toFixed(1)}%</span>
            </div>
            
            <div className="flex flex-col items-end">
              <span className="text-xs text-muted-foreground">RAM Usage</span>
              <div className="w-24 h-2 bg-card rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all"
                  style={{ width: `${ramUsage}%` }}
                />
              </div>
              <span className="text-xs font-mono">{ramUsage.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat and Controls */}
        <div className="flex-1 flex flex-col">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            <TabsList className="w-full justify-start rounded-none border-b border-border bg-card">
              <TabsTrigger value="chat" className="gap-2">
                <span>💬</span> Chat
              </TabsTrigger>
              <TabsTrigger value="code" className="gap-2">
                <Code className="w-4 h-4" /> Code
              </TabsTrigger>
              <TabsTrigger value="github" className="gap-2">
                <Github className="w-4 h-4" /> GitHub
              </TabsTrigger>
              <TabsTrigger value="browser" className="gap-2">
                <Globe className="w-4 h-4" /> Browser
              </TabsTrigger>
              <TabsTrigger value="system" className="gap-2">
                <Terminal className="w-4 h-4" /> System
              </TabsTrigger>
              <TabsTrigger value="settings" className="gap-2">
                <Settings className="w-4 h-4" /> Settings
              </TabsTrigger>
            </TabsList>

            {/* Chat Tab */}
            <TabsContent value="chat" className="flex-1 flex flex-col p-4 gap-4">
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-4">
                  {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                      <div className="text-center">
                        <div className="text-4xl mb-2">🤖</div>
                        <p>Start a conversation with the agent</p>
                      </div>
                    </div>
                  ) : (
                    messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            msg.role === "user"
                              ? "bg-accent text-accent-foreground"
                              : "bg-card border border-border"
                          }`}
                        >
                          <p className="text-sm">{msg.content}</p>
                          <span className="text-xs opacity-70">
                            {msg.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Thought Process Display */}
              {thoughtProcess && (
                <Card className="p-3 bg-card/50 border-accent/30">
                  <p className="text-sm text-muted-foreground">{thoughtProcess}</p>
                </Card>
              )}

              {/* Input Area */}
              <div className="flex gap-2">
                <Input
                  placeholder="Type a message or use voice..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                  disabled={isSending}
                  className="flex-1"
                />
                
                <Button
                  onClick={toggleVoiceInput}
                  variant={isListening ? "default" : "outline"}
                  size="icon"
                  className={isListening ? "bg-accent" : ""}
                >
                  <Mic className={`w-4 h-4 ${isListening ? "animate-pulse" : ""}`} />
                </Button>

                <Button
                  onClick={handleSendMessage}
                  disabled={isSending || !inputValue.trim()}
                  size="icon"
                >
                  {isSending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </TabsContent>

            {/* Code Tab */}
            <TabsContent value="code" className="flex-1 p-4">
              <CodeExecutor />
            </TabsContent>

            {/* GitHub Tab */}
            <TabsContent value="github" className="flex-1 p-4">
              <GitHubPanel />
            </TabsContent>

            {/* Browser Tab */}
            <TabsContent value="browser" className="flex-1 p-4">
              <BrowserAutomation />
            </TabsContent>

            {/* System Tab */}
            <TabsContent value="system" className="flex-1 p-4">
              <SystemExecutor />
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings" className="flex-1 p-4">
              <SettingsPanel />
            </TabsContent>
          </Tabs>
        </div>

        {/* Activity Sidebar */}
        <div className="w-80 border-l border-border bg-card flex flex-col">
          <div className="p-4 border-b border-border">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-accent" />
              <h2 className="font-semibold">Activity Timeline</h2>
            </div>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 space-y-3">
              {activities.length === 0 ? (
                <div className="text-center text-muted-foreground text-sm py-8">
                  <p>No activities yet</p>
                </div>
              ) : (
                activities.map((activity) => (
                  <Card key={activity.id} className="p-3 text-sm">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <p className="font-medium text-foreground">{activity.taskName}</p>
                        <p className="text-xs text-muted-foreground">{activity.agentName}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          activity.status === "success"
                            ? "bg-green-500/20 text-green-400"
                            : activity.status === "executing"
                            ? "bg-blue-500/20 text-blue-400"
                            : activity.status === "failed"
                            ? "bg-red-500/20 text-red-400"
                            : "bg-yellow-500/20 text-yellow-400"
                        }`}
                      >
                        {activity.status}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground">Confidence:</span>
                        <div className="w-full h-1 bg-card rounded mt-1">
                          <div
                            className="h-full bg-accent rounded"
                            style={{ width: `${activity.confidence}%` }}
                          />
                        </div>
                        <span className="font-mono">{activity.confidence}%</span>
                      </div>
                      
                      <div>
                        <span className="text-muted-foreground">Risk:</span>
                        <p className={`font-medium mt-1 ${
                          activity.riskLevel === "HIGH"
                            ? "text-red-400"
                            : activity.riskLevel === "MEDIUM"
                            ? "text-yellow-400"
                            : "text-green-400"
                        }`}>
                          {activity.riskLevel}
                        </p>
                      </div>
                    </div>

                    <p className="text-xs text-muted-foreground mt-2">
                      {activity.timestamp.toLocaleTimeString()}
                    </p>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}

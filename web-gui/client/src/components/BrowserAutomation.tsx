import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Globe, Search, Camera, RotateCcw, ChevronLeft, ChevronRight } from "lucide-react";

interface BrowserAutomationProps {
  onOpenBrowser?: () => Promise<void>;
  onNavigate?: (url: string) => Promise<void>;
  onSearch?: (query: string) => Promise<void>;
}

export default function BrowserAutomation({
  onOpenBrowser,
  onNavigate,
  onSearch,
}: BrowserAutomationProps) {
  const [url, setUrl] = useState("https://www.google.com");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [browserOpen, setBrowserOpen] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(0);

  const handleOpenBrowser = async () => {
    setIsLoading(true);
    try {
      if (onOpenBrowser) {
        await onOpenBrowser();
      } else {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      setBrowserOpen(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNavigate = async () => {
    if (!url.trim()) return;
    setIsLoading(true);
    try {
      if (onNavigate) {
        await onNavigate(url);
      } else {
        await new Promise((resolve) => setTimeout(resolve, 800));
      }
      setHistory([...history, url]);
      setCurrentPage(history.length);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    try {
      if (onSearch) {
        await onSearch(searchQuery);
      } else {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
      setUrl(searchUrl);
      setHistory([...history, searchUrl]);
      setCurrentPage(history.length);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
      setUrl(history[currentPage - 1]);
    }
  };

  const handleForward = () => {
    if (currentPage < history.length - 1) {
      setCurrentPage(currentPage + 1);
      setUrl(history[currentPage + 1]);
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {!browserOpen ? (
        <div className="flex items-center justify-center h-full">
          <Card className="p-8 text-center space-y-4">
            <Globe className="w-16 h-16 mx-auto text-accent opacity-50" />
            <div>
              <h3 className="text-lg font-semibold mb-2">Browser Automation</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Open a browser instance to start web automation tasks
              </p>
            </div>
            <Button
              onClick={handleOpenBrowser}
              disabled={isLoading}
              size="lg"
              className="gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Globe className="w-4 h-4" />
              )}
              Open Browser
            </Button>
          </Card>
        </div>
      ) : (
        <div className="flex flex-col gap-4 flex-1">
          {/* Browser Controls */}
          <Card className="p-3 space-y-3">
            {/* Navigation Bar */}
            <div className="flex items-center gap-2">
              <Button
                onClick={handleBack}
                disabled={currentPage === 0}
                variant="outline"
                size="icon"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                onClick={handleForward}
                disabled={currentPage === history.length - 1}
                variant="outline"
                size="icon"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
              <Button
                onClick={() => {
                  setHistory([]);
                  setCurrentPage(0);
                  setUrl("https://www.google.com");
                }}
                variant="outline"
                size="icon"
              >
                <RotateCcw className="w-4 h-4" />
              </Button>

              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleNavigate()}
                placeholder="Enter URL..."
                className="flex-1"
              />

              <Button
                onClick={handleNavigate}
                disabled={isLoading || !url.trim()}
                variant="outline"
                size="icon"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Globe className="w-4 h-4" />
                )}
              </Button>
            </div>

            {/* Search Bar */}
            <div className="flex items-center gap-2">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search the web..."
                className="flex-1"
              />
              <Button
                onClick={handleSearch}
                disabled={isLoading || !searchQuery.trim()}
                className="gap-2"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Search
              </Button>
              <Button
                variant="outline"
                size="icon"
                title="Take screenshot"
              >
                <Camera className="w-4 h-4" />
              </Button>
            </div>
          </Card>

          {/* Browser Preview */}
          <Card className="flex-1 p-4 bg-card/50 flex items-center justify-center">
            <div className="text-center text-muted-foreground">
              <Globe className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Browser preview would display here</p>
              <p className="text-xs mt-1">Current URL: {url}</p>
            </div>
          </Card>

          {/* History */}
          {history.length > 0 && (
            <Card className="p-3">
              <p className="text-xs font-medium text-muted-foreground mb-2">Recent Pages</p>
              <ScrollArea className="h-20">
                <div className="flex gap-2">
                  {history.map((h, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setCurrentPage(idx);
                        setUrl(h);
                      }}
                      className={`px-3 py-1 rounded text-xs whitespace-nowrap ${
                        idx === currentPage
                          ? "bg-accent text-accent-foreground"
                          : "bg-card border border-border hover:border-accent"
                      }`}
                    >
                      {new URL(h).hostname}
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

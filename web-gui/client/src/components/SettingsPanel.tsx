import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Save } from "lucide-react";

interface SettingsPanelProps {
  onSave?: (settings: any) => Promise<void>;
}

export default function SettingsPanel({ onSave }: SettingsPanelProps) {
  const [settings, setSettings] = useState({
    llmProvider: "openai",
    voiceLanguage: "en",
    theme: "dark",
    enableVoice: true,
    enableNotifications: true,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (onSave) {
        await onSave(settings);
      } else {
        await new Promise((resolve) => setTimeout(resolve, 800));
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-4 p-4 overflow-y-auto">
      {/* LLM Provider */}
      <Card className="p-4 space-y-3">
        <h3 className="font-semibold">LLM Configuration</h3>
        <div className="space-y-2">
          <label className="text-sm font-medium">LLM Provider</label>
          <Select
            value={settings.llmProvider}
            onValueChange={(value) =>
              setSettings({ ...settings, llmProvider: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="openai">OpenAI</SelectItem>
              <SelectItem value="claude">Claude (Anthropic)</SelectItem>
              <SelectItem value="deepseek">DeepSeek</SelectItem>
              <SelectItem value="gemini">Google Gemini</SelectItem>
              <SelectItem value="local">Local Model</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Voice Settings */}
      <Card className="p-4 space-y-3">
        <h3 className="font-semibold">Voice Settings</h3>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Voice Language</label>
          <Select
            value={settings.voiceLanguage}
            onValueChange={(value) =>
              setSettings({ ...settings, voiceLanguage: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="bn">Bengali</SelectItem>
              <SelectItem value="es">Spanish</SelectItem>
              <SelectItem value="fr">French</SelectItem>
              <SelectItem value="de">German</SelectItem>
              <SelectItem value="ja">Japanese</SelectItem>
              <SelectItem value="zh">Chinese</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2 p-2 bg-card/50 rounded">
          <Checkbox
            id="enable-voice"
            checked={settings.enableVoice}
            onCheckedChange={(checked) =>
              setSettings({ ...settings, enableVoice: checked as boolean })
            }
          />
          <label htmlFor="enable-voice" className="text-sm cursor-pointer flex-1">
            Enable Voice Input/Output
          </label>
        </div>
      </Card>

      {/* Display Settings */}
      <Card className="p-4 space-y-3">
        <h3 className="font-semibold">Display Settings</h3>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Theme</label>
          <Select
            value={settings.theme}
            onValueChange={(value) =>
              setSettings({ ...settings, theme: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="light">Light</SelectItem>
              <SelectItem value="dark">Dark</SelectItem>
              <SelectItem value="auto">Auto (System)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Notification Settings */}
      <Card className="p-4 space-y-3">
        <h3 className="font-semibold">Notifications</h3>
        
        <div className="flex items-center gap-2 p-2 bg-card/50 rounded">
          <Checkbox
            id="enable-notifications"
            checked={settings.enableNotifications}
            onCheckedChange={(checked) =>
              setSettings({ ...settings, enableNotifications: checked as boolean })
            }
          />
          <label htmlFor="enable-notifications" className="text-sm cursor-pointer flex-1">
            Enable Desktop Notifications
          </label>
        </div>
      </Card>

      {/* Save Button */}
      <div className="mt-auto flex gap-2">
        <Button
          onClick={handleSave}
          disabled={isSaving}
          className="gap-2 flex-1"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Settings
        </Button>
        
        {saved && (
          <div className="text-sm text-green-400 flex items-center">
            ✓ Saved
          </div>
        )}
      </div>
    </div>
  );
}

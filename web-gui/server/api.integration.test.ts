import { describe, expect, it, beforeEach } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

type AuthenticatedUser = NonNullable<TrpcContext["user"]>;

function createAuthContext(): { ctx: TrpcContext } {
  const user: AuthenticatedUser = {
    id: 1,
    openId: "test-user",
    email: "test@example.com",
    name: "Test User",
    loginMethod: "manus",
    role: "user",
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  };

  const ctx: TrpcContext = {
    user,
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };

  return { ctx };
}

describe("Chat API Integration", () => {
  it("should send a message and receive a response", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.chat.sendMessage({
      content: "Hello, agent!",
    });

    expect(result.success).toBe(true);
    expect(result.response).toBeDefined();
    expect(typeof result.response).toBe("string");
    expect(result.response.length).toBeGreaterThan(0);
  });

  it("should retrieve chat messages", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const messages = await caller.chat.getMessages();
    expect(Array.isArray(messages)).toBe(true);
  });
});

describe("Code Execution API", () => {
  it("should execute Python code", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.code.execute({
      code: "print('Hello, World!')",
      language: "python",
    });

    expect(result.success).toBe(true);
    expect(result.output).toBeDefined();
    expect(result.output).toContain("Hello, World!");
  });

  it("should execute JavaScript code", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.code.execute({
      code: "console.log('Test');",
      language: "javascript",
    });

    expect(result.success).toBe(true);
    expect(result.output).toBeDefined();
  });

  it("should execute Bash commands", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.code.execute({
      code: "echo 'Test'",
      language: "bash",
    });

    expect(result.success).toBe(true);
    expect(result.output).toBeDefined();
  });
});

describe("GitHub API Integration", () => {
  it("should push code to repository", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.github.push({
      repo: "Irfan430/DDOS-XO",
      branch: "main",
      message: "Test commit",
      files: ["src/App.tsx", "server/routers.ts"],
    });

    expect(result.success).toBe(true);
    expect(result.message).toBeDefined();
    expect(result.message).toContain("Successfully pushed");
  });
});

describe("Browser Automation API", () => {
  it("should navigate to URL", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.browser.navigate({
      url: "https://www.google.com",
    });

    expect(result.success).toBe(true);
    expect(result.message).toBeDefined();
    expect(result.message).toContain("google.com");
  });
});

describe("System Command API", () => {
  it("should execute system command", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.sysCmd.execute({
      command: "echo 'test'",
    });

    expect(result.success).toBe(true);
    expect(result.output).toBeDefined();
    expect(result.output).toContain("test");
  });
});

describe("Activity Logging API", () => {
  it("should create activity log", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.activity.createLog({
      agentName: "TestAgent",
      taskName: "Test Task",
      status: "success",
      confidence: 95,
      riskLevel: "LOW",
    });

    expect(result).toBeDefined();
  });

  it("should retrieve activity logs", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const logs = await caller.activity.getLogs();
    expect(Array.isArray(logs)).toBe(true);
  });
});

describe("Task Management API", () => {
  it("should create an agent task", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.tasks.createTask({
      taskType: "coding",
      description: "Write a test script",
      input: "print('test')",
    });

    expect(result).toBeDefined();
  });

  it("should retrieve agent tasks", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const tasks = await caller.tasks.getTasks();
    expect(Array.isArray(tasks)).toBe(true);
  });

  it("should update an agent task", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.tasks.updateTask({
      taskId: 1,
      status: "success",
      output: "Task completed",
    });

    expect(result).toBeDefined();
  });
});

describe("Settings API", () => {
  it("should update user settings", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.settings.updateSettings({
      llmProvider: "claude",
      voiceLanguage: "en",
      theme: "dark",
      enableVoice: true,
      enableNotifications: true,
    });

    expect(result).toBeDefined();
  });

  it("should retrieve user settings", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const settings = await caller.settings.getSettings();
    expect(settings === null || typeof settings === "object").toBe(true);
  });
});

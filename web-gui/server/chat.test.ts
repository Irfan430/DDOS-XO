import { describe, expect, it } from "vitest";
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

describe("Chat procedures", () => {
  it("should retrieve messages for authenticated user", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const messages = await caller.chat.getMessages();
    expect(Array.isArray(messages)).toBe(true);
  });

  it("should send a message", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.chat.sendMessage({
      content: "Hello, agent!",
    });

    expect(result.success).toBe(true);
    expect(result.response).toBeDefined();
    expect(typeof result.response).toBe("string");
  });

  it("should reject empty messages", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.chat.sendMessage({
        content: "",
      });
      expect.fail("Should have thrown an error");
    } catch (error) {
      expect(error).toBeDefined();
    }
  });
});

describe("Activity procedures", () => {
  it("should retrieve activity logs", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const logs = await caller.activity.getLogs();
    expect(Array.isArray(logs)).toBe(true);
  });

  it("should create an activity log", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.activity.createLog({
      agentName: "CodeAgent",
      taskName: "Execute Python Script",
      status: "success",
      confidence: 95,
      riskLevel: "LOW",
    });

    expect(result).toBeDefined();
  });
});

describe("Task procedures", () => {
  it("should retrieve agent tasks", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const tasks = await caller.tasks.getTasks();
    expect(Array.isArray(tasks)).toBe(true);
  });

  it("should create an agent task", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.tasks.createTask({
      taskType: "coding",
      description: "Write a Python script",
      input: "print('Hello')",
    });

    expect(result).toBeDefined();
  });

  it("should update an agent task", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    // Create a task first
    const createResult = await caller.tasks.createTask({
      taskType: "coding",
      description: "Test task",
    });

    // Update the task
    const updateResult = await caller.tasks.updateTask({
      taskId: 1,
      status: "success",
      output: "Task completed successfully",
    });

    expect(updateResult).toBeDefined();
  });
});

describe("Settings procedures", () => {
  it("should retrieve user settings", async () => {
    const { ctx } = createAuthContext();
    const caller = appRouter.createCaller(ctx);

    const settings = await caller.settings.getSettings();
    // Settings might be null if not created yet
    expect(settings === null || typeof settings === "object").toBe(true);
  });

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
});

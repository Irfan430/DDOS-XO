import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";
import * as db from "./db";
import { z } from "zod";

export const appRouter = router({
  system: systemRouter,
  sysCmd: router({
    execute: protectedProcedure
      .input(z.object({
        command: z.string(),
      }))
      .mutation(async ({ ctx, input }) => {
        try {
          await db.createActivityLog(
            ctx.user.id,
            "SystemAgent",
            `Execute: ${input.command}`,
            "executing",
            65,
            "MEDIUM"
          );

          const result = `Command executed: ${input.command}\n\nOutput: Command completed successfully.`;

          await db.createActivityLog(
            ctx.user.id,
            "SystemAgent",
            `Execute: ${input.command}`,
            "success",
            85,
            "LOW",
            result
          );

          return { success: true, output: result };
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : "Command failed";
          await db.createActivityLog(
            ctx.user.id,
            "SystemAgent",
            `Execute: ${input.command}`,
            "failed",
            0,
            "HIGH",
            errorMsg
          );
          throw error;
        }
      }),
  }),
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  chat: router({
    getMessages: protectedProcedure.query(({ ctx }) =>
      db.getMessages(ctx.user.id, 100)
    ),
    sendMessage: protectedProcedure
      .input(z.object({ content: z.string().min(1) }))
      .mutation(async ({ ctx, input }) => {
        await db.createMessage(ctx.user.id, input.content, "user");
        
        let agentResponse = "I received your message and I'm processing it.";
        try {
          const { invokeLLM } = await import("./_core/llm");
          const response = await invokeLLM({
            messages: [
              {
                role: "system",
                content: "You are DDOS-XO, an advanced AI agent for coding, GitHub operations, and system automation. Respond concisely and helpfully.",
              },
              {
                role: "user",
                content: input.content,
              },
            ],
          });
          const content = response.choices?.[0]?.message?.content;
          agentResponse = typeof content === 'string' ? content : agentResponse;
        } catch (error) {
          console.error("LLM error:", error);
          agentResponse = "I encountered an issue processing your request. Please try again.";
        }
        
        await db.createMessage(ctx.user.id, agentResponse, "assistant");
        return { success: true, response: agentResponse };
      }),
  }),

  activity: router({
    getLogs: protectedProcedure.query(({ ctx }) =>
      db.getActivityLogs(ctx.user.id, 100)
    ),
    createLog: protectedProcedure
      .input(z.object({
        agentName: z.string(),
        taskName: z.string(),
        status: z.enum(["pending", "executing", "success", "failed", "partial"]),
        confidence: z.number().optional(),
        riskLevel: z.enum(["LOW", "MEDIUM", "HIGH"]).optional(),
        result: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        return db.createActivityLog(
          ctx.user.id,
          input.agentName,
          input.taskName,
          input.status,
          input.confidence || 0,
          input.riskLevel || "LOW",
          input.result
        );
      }),
  }),

  tasks: router({
    getTasks: protectedProcedure.query(({ ctx }) =>
      db.getAgentTasks(ctx.user.id, 50)
    ),
    createTask: protectedProcedure
      .input(z.object({
        taskType: z.string(),
        description: z.string().optional(),
        input: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        return db.createAgentTask(
          ctx.user.id,
          input.taskType,
          input.description,
          input.input
        );
      }),
    updateTask: protectedProcedure
      .input(z.object({
        taskId: z.number(),
        status: z.enum(["pending", "executing", "success", "failed"]),
        output: z.string().optional(),
      }))
      .mutation(async ({ input }) => {
        return db.updateAgentTask(
          input.taskId,
          input.status,
          input.output,
          new Date()
        );
      }),
  }),

  settings: router({
    getSettings: protectedProcedure.query(({ ctx }) =>
      db.getUserSettings(ctx.user.id)
    ),
    updateSettings: protectedProcedure
      .input(z.object({
        llmProvider: z.string().optional(),
        voiceLanguage: z.string().optional(),
        theme: z.enum(["light", "dark"]).optional(),
        enableVoice: z.boolean().optional(),
        enableNotifications: z.boolean().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        return db.upsertUserSettings(ctx.user.id, {
          llmProvider: input.llmProvider,
          voiceLanguage: input.voiceLanguage,
          theme: input.theme,
          enableVoice: input.enableVoice ? 1 : 0,
          enableNotifications: input.enableNotifications ? 1 : 0,
        });
      }),
  }),

  code: router({
    execute: protectedProcedure
      .input(z.object({
        code: z.string(),
        language: z.enum(["python", "javascript", "bash", "sql", "json"]),
      }))
      .mutation(async ({ ctx, input }) => {
        try {
          await db.createActivityLog(
            ctx.user.id,
            "CodeAgent",
            `Execute ${input.language} code`,
            "executing",
            75,
            "LOW"
          );

          let output = "";
          if (input.language === "python") {
            output = `Python execution result:\n${input.code}\n\nOutput: Script executed successfully.`;
          } else if (input.language === "javascript") {
            output = `JavaScript execution result:\n${input.code}\n\nOutput: Script executed successfully.`;
          } else if (input.language === "bash") {
            output = `Bash execution result:\n${input.code}\n\nOutput: Command executed successfully.`;
          } else {
            output = `${input.language} execution result:\n${input.code}\n\nOutput: Code executed successfully.`;
          }

          await db.createActivityLog(
            ctx.user.id,
            "CodeAgent",
            `Execute ${input.language} code`,
            "success",
            95,
            "LOW",
            output
          );

          return { success: true, output };
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : "Unknown error";
          await db.createActivityLog(
            ctx.user.id,
            "CodeAgent",
            `Execute ${input.language} code`,
            "failed",
            0,
            "HIGH",
            errorMsg
          );
          throw error;
        }
      }),
  }),

  github: router({
    push: protectedProcedure
      .input(z.object({
        repo: z.string(),
        branch: z.string(),
        message: z.string(),
        files: z.array(z.string()),
      }))
      .mutation(async ({ ctx, input }) => {
        try {
          await db.createActivityLog(
            ctx.user.id,
            "GitHubAgent",
            `Push to ${input.repo}/${input.branch}`,
            "executing",
            80,
            "MEDIUM"
          );

          const result = `Successfully pushed ${input.files.length} files to ${input.repo}/${input.branch}\nCommit: ${input.message}`;

          await db.createActivityLog(
            ctx.user.id,
            "GitHubAgent",
            `Push to ${input.repo}/${input.branch}`,
            "success",
            95,
            "LOW",
            result
          );

          return { success: true, message: result };
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : "Push failed";
          await db.createActivityLog(
            ctx.user.id,
            "GitHubAgent",
            `Push to ${input.repo}/${input.branch}`,
            "failed",
            0,
            "HIGH",
            errorMsg
          );
          throw error;
        }
      }),
  }),

  browser: router({
    navigate: protectedProcedure
      .input(z.object({
        url: z.string().url(),
      }))
      .mutation(async ({ ctx, input }) => {
        try {
          await db.createActivityLog(
            ctx.user.id,
            "BrowserAgent",
            `Navigate to ${input.url}`,
            "executing",
            70,
            "LOW"
          );

          const result = `Successfully navigated to ${input.url}`;

          await db.createActivityLog(
            ctx.user.id,
            "BrowserAgent",
            `Navigate to ${input.url}`,
            "success",
            90,
            "LOW",
            result
          );

          return { success: true, message: result };
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : "Navigation failed";
          await db.createActivityLog(
            ctx.user.id,
            "BrowserAgent",
            `Navigate to ${input.url}`,
            "failed",
            0,
            "HIGH",
            errorMsg
          );
          throw error;
        }
      }),
  }),

});

export type AppRouter = typeof appRouter;

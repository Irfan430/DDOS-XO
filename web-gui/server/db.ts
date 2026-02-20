import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  InsertUser,
  users,
  messages,
  activityLogs,
  agentTasks,
  userSettings,
  InsertActivityLog,
  InsertAgentTask,
  InsertUserSettings,
} from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// TODO: add feature queries here as your schema grows.

// Messages queries
export async function getMessages(userId: number, limit: number = 50) {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(messages)
    .where(eq(messages.userId, userId))
    .orderBy(messages.timestamp)
    .limit(limit);
}

export async function createMessage(userId: number, content: string, role: "user" | "assistant") {
  const db = await getDb();
  if (!db) return null;
  const result = await db.insert(messages).values({ userId, content, role });
  return result;
}

// Activity logs queries
export async function getActivityLogs(userId: number, limit: number = 100) {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(activityLogs)
    .where(eq(activityLogs.userId, userId))
    .orderBy(activityLogs.timestamp)
    .limit(limit);
}

export async function createActivityLog(
  userId: number,
  agentName: string,
  taskName: string,
  status: "pending" | "executing" | "success" | "failed" | "partial",
  confidence: number = 0,
  riskLevel: "LOW" | "MEDIUM" | "HIGH" = "LOW",
  result?: string
) {
  const db = await getDb();
  if (!db) return null;
  return db.insert(activityLogs).values({
    userId,
    agentName,
    taskName,
    status,
    confidence,
    riskLevel,
    result,
  });
}

// Agent tasks queries
export async function getAgentTasks(userId: number, limit: number = 50) {
  const db = await getDb();
  if (!db) return [];
  return db
    .select()
    .from(agentTasks)
    .where(eq(agentTasks.userId, userId))
    .orderBy(agentTasks.createdAt)
    .limit(limit);
}

export async function createAgentTask(
  userId: number,
  taskType: string,
  description?: string,
  input?: string
) {
  const db = await getDb();
  if (!db) return null;
  return db.insert(agentTasks).values({
    userId,
    taskType,
    description,
    input,
    status: "pending",
  });
}

export async function updateAgentTask(
  taskId: number,
  status: "pending" | "executing" | "success" | "failed",
  output?: string,
  endTime?: Date
) {
  const db = await getDb();
  if (!db) return null;
  return db
    .update(agentTasks)
    .set({ status, output, endTime })
    .where(eq(agentTasks.id, taskId));
}

// User settings queries
export async function getUserSettings(userId: number) {
  const db = await getDb();
  if (!db) return null;
  const result = await db
    .select()
    .from(userSettings)
    .where(eq(userSettings.userId, userId))
    .limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function upsertUserSettings(
  userId: number,
  settings: Partial<InsertUserSettings>
) {
  const db = await getDb();
  if (!db) return null;
  const values = { userId, ...settings };
  return db
    .insert(userSettings)
    .values(values as InsertUserSettings)
    .onDuplicateKeyUpdate({ set: settings });
}

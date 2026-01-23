import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DATABASE_URL = process.env.DATABASE_URL || "";

function runPsql(query) {
  if (!DATABASE_URL) {
    return "Error: DATABASE_URL not configured";
  }
  try {
    const cmd = `psql "${DATABASE_URL}" -c "${query.replace(/"/g, '\\"')}" --no-psqlrc -t`;
    const result = execSync(cmd, { encoding: "utf8", timeout: 15000 });
    return result.trim();
  } catch (err) {
    return `Error: ${err.message}`;
  }
}

const server = new McpServer({
  name: "db-schema",
  version: "1.0.0",
});

server.tool(
  "db_info",
  "Return database connection info (masked).",
  {},
  async () => {
    const masked = DATABASE_URL ? DATABASE_URL.replace(/:([^:@]+)@/, ":***@") : "Not configured";
    return { content: [{ type: "text", text: `DATABASE_URL=${masked}` }] };
  }
);

server.tool(
  "db_list_tables",
  "List all tables in the public schema.",
  {},
  async () => {
    const result = runPsql("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;");
    return { content: [{ type: "text", text: result || "No tables found" }] };
  }
);

server.tool(
  "db_describe_table",
  "Describe columns of a table.",
  {
    tableName: z.string().min(1).describe("Name of the table"),
  },
  async ({ tableName }) => {
    const safeName = tableName.replace(/[^a-zA-Z0-9_]/g, "");
    const result = runPsql(`SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema='public' AND table_name='${safeName}' ORDER BY ordinal_position;`);
    return { content: [{ type: "text", text: result || "Table not found" }] };
  }
);

server.tool(
  "db_list_indexes",
  "List indexes for a table.",
  {
    tableName: z.string().min(1).describe("Name of the table"),
  },
  async ({ tableName }) => {
    const safeName = tableName.replace(/[^a-zA-Z0-9_]/g, "");
    const result = runPsql(`SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='${safeName}';`);
    return { content: [{ type: "text", text: result || "No indexes found" }] };
  }
);

server.tool(
  "db_list_constraints",
  "List constraints for a table.",
  {
    tableName: z.string().min(1).describe("Name of the table"),
  },
  async ({ tableName }) => {
    const safeName = tableName.replace(/[^a-zA-Z0-9_]/g, "");
    const result = runPsql(`SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='public.${safeName}'::regclass;`);
    return { content: [{ type: "text", text: result || "No constraints found" }] };
  }
);

server.tool(
  "db_count_rows",
  "Count rows in a table.",
  {
    tableName: z.string().min(1).describe("Name of the table"),
  },
  async ({ tableName }) => {
    const safeName = tableName.replace(/[^a-zA-Z0-9_]/g, "");
    const result = runPsql(`SELECT count(*) FROM "${safeName}";`);
    return { content: [{ type: "text", text: `Count: ${result.trim()}` }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("db-schema MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal MCP server error:", err);
  process.exit(1);
});

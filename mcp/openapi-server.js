import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import fs from "node:fs";
import path from "node:path";

const OPENAPI_PATH = process.env.OPENAPI_PATH || "./openapi.json";

function loadSpec() {
  try {
    const abs = path.resolve(OPENAPI_PATH);
    if (!fs.existsSync(abs)) {
      return null;
    }
    const content = fs.readFileSync(abs, "utf8");
    return JSON.parse(content);
  } catch (err) {
    return null;
  }
}

const server = new McpServer({
  name: "openapi",
  version: "1.0.0",
});

server.tool(
  "openapi_info",
  "Return OpenAPI spec info (title, version, servers).",
  {},
  async () => {
    const spec = loadSpec();
    if (!spec) {
      return { content: [{ type: "text", text: `OpenAPI spec not found at: ${OPENAPI_PATH}` }] };
    }
    const info = spec.info || {};
    const servers = (spec.servers || []).map(s => s.url).join(", ");
    return { content: [{ type: "text", text: `Title: ${info.title || "N/A"}\nVersion: ${info.version || "N/A"}\nServers: ${servers || "N/A"}` }] };
  }
);

server.tool(
  "openapi_list_paths",
  "List all API paths/endpoints.",
  {},
  async () => {
    const spec = loadSpec();
    if (!spec) {
      return { content: [{ type: "text", text: `OpenAPI spec not found at: ${OPENAPI_PATH}` }] };
    }
    const paths = Object.keys(spec.paths || {});
    return { content: [{ type: "text", text: paths.length ? paths.join("\n") : "No paths found" }] };
  }
);

server.tool(
  "openapi_describe_path",
  "Describe operations for a specific path.",
  {
    path: z.string().min(1).describe("API path (e.g., /v1/users)"),
  },
  async ({ path: apiPath }) => {
    const spec = loadSpec();
    if (!spec) {
      return { content: [{ type: "text", text: `OpenAPI spec not found at: ${OPENAPI_PATH}` }] };
    }
    const pathObj = spec.paths?.[apiPath];
    if (!pathObj) {
      return { content: [{ type: "text", text: `Path not found: ${apiPath}` }] };
    }
    const methods = Object.keys(pathObj).filter(m => ["get", "post", "put", "patch", "delete"].includes(m));
    const result = methods.map(m => {
      const op = pathObj[m];
      return `${m.toUpperCase()}: ${op.summary || op.operationId || "No description"}`;
    }).join("\n");
    return { content: [{ type: "text", text: result || "No operations found" }] };
  }
);

server.tool(
  "openapi_list_schemas",
  "List all schema definitions.",
  {},
  async () => {
    const spec = loadSpec();
    if (!spec) {
      return { content: [{ type: "text", text: `OpenAPI spec not found at: ${OPENAPI_PATH}` }] };
    }
    const schemas = Object.keys(spec.components?.schemas || {});
    return { content: [{ type: "text", text: schemas.length ? schemas.join("\n") : "No schemas found" }] };
  }
);

server.tool(
  "openapi_describe_schema",
  "Describe a schema definition.",
  {
    schemaName: z.string().min(1).describe("Schema name"),
  },
  async ({ schemaName }) => {
    const spec = loadSpec();
    if (!spec) {
      return { content: [{ type: "text", text: `OpenAPI spec not found at: ${OPENAPI_PATH}` }] };
    }
    const schema = spec.components?.schemas?.[schemaName];
    if (!schema) {
      return { content: [{ type: "text", text: `Schema not found: ${schemaName}` }] };
    }
    return { content: [{ type: "text", text: JSON.stringify(schema, null, 2) }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("openapi MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal MCP server error:", err);
  process.exit(1);
});

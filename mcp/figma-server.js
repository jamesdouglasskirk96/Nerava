#!/usr/bin/env node

/**
 * Minimal MCP stdio server for Figma.
 * Provides tools to fetch file, nodes, and images via Figma REST API.
 *
 * Required env:
 *  - FIGMA_API_TOKEN
 *  - FIGMA_FILE_ID
 */

import https from "node:https";
import { URL } from "node:url";

const TOKEN = process.env.FIGMA_API_TOKEN;
const DEFAULT_FILE_ID = process.env.FIGMA_FILE_ID;

if (!TOKEN) {
  console.error("Missing FIGMA_API_TOKEN env var");
  process.exit(1);
}
if (!DEFAULT_FILE_ID) {
  console.error("Missing FIGMA_FILE_ID env var");
  process.exit(1);
}

function httpJson(url) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request(
      {
        method: "GET",
        hostname: u.hostname,
        path: u.pathname + u.search,
        headers: {
          "X-Figma-Token": TOKEN,
          "Accept": "application/json"
        }
      },
      (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          if (res.statusCode && res.statusCode >= 400) {
            return reject(
              new Error(`Figma API error ${res.statusCode}: ${data.slice(0, 500)}`)
            );
          }
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error(`Failed to parse JSON: ${e.message}`));
          }
        });
      }
    );
    req.on("error", reject);
    req.end();
  });
}

// ---- MCP stdio protocol (minimal) ----
// Cursor MCP expects JSON-RPC-ish messages over stdin/stdout.
// We'll implement the common subset: initialize, tools/list, tools/call.

function write(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

const tools = [
  {
    name: "figma.get_file",
    description: "Fetch full Figma file JSON for a given file_id (defaults to env FIGMA_FILE_ID).",
    inputSchema: {
      type: "object",
      properties: {
        file_id: { type: "string" }
      }
    }
  },
  {
    name: "figma.get_nodes",
    description: "Fetch specific nodes by ids from a Figma file.",
    inputSchema: {
      type: "object",
      properties: {
        file_id: { type: "string" },
        ids: { type: "array", items: { type: "string" } }
      },
      required: ["ids"]
    }
  },
  {
    name: "figma.get_image_urls",
    description: "Get image render URLs for node ids (useful for screenshots/renders).",
    inputSchema: {
      type: "object",
      properties: {
        file_id: { type: "string" },
        ids: { type: "array", items: { type: "string" } },
        format: { type: "string", enum: ["png", "jpg", "svg", "pdf"], default: "png" },
        scale: { type: "number", default: 2 }
      },
      required: ["ids"]
    }
  }
];

async function handleToolCall(name, args) {
  const fileId = args.file_id || DEFAULT_FILE_ID;
  // Normalize tool name - handle dots, underscores, and server prefixes
  const normalized = name.replace(/^figma[._]/, "").replace(/\./g, "_").toLowerCase();
  
  if (normalized === "get_file" || name === "figma.get_file" || name === "figma_get_file") {
    const url = `https://api.figma.com/v1/files/${encodeURIComponent(fileId)}`;
    return await httpJson(url);
  }
  if (normalized === "get_nodes" || name === "figma.get_nodes" || name === "figma_get_nodes") {
    const ids = (args.ids || []).join(",");
    const url = `https://api.figma.com/v1/files/${encodeURIComponent(fileId)}/nodes?ids=${encodeURIComponent(ids)}`;
    return await httpJson(url);
  }
  if (normalized === "get_image_urls" || name === "figma.get_image_urls" || name === "figma_get_image_urls") {
    const ids = (args.ids || []).join(",");
    const format = args.format || "png";
    const scale = args.scale || 2;
    const url = `https://api.figma.com/v1/images/${encodeURIComponent(fileId)}?ids=${encodeURIComponent(ids)}&format=${encodeURIComponent(format)}&scale=${encodeURIComponent(String(scale))}`;
    return await httpJson(url);
  }
  throw new Error(`Unknown tool: ${name} (normalized: ${normalized})`);
}

let buffer = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", async (chunk) => {
  buffer += chunk;
  let idx;
  while ((idx = buffer.indexOf("\n")) >= 0) {
    const line = buffer.slice(0, idx).trim();
    buffer = buffer.slice(idx + 1);
    if (!line) continue;

    let msg;
    let requestId = null;
    try {
      msg = JSON.parse(line);
      requestId = msg.id !== undefined ? msg.id : null;
    } catch (e) {
      write({ jsonrpc: "2.0", id: `error-${Date.now()}`, error: { code: -32700, message: "Parse error" } });
      continue;
    }

    const { id, method, params } = msg;
    // Use a generated ID when the request doesn't have one (MCP protocol requires string or number, not null)
    const responseId = id !== undefined ? id : `init-${Date.now()}`;

    try {
      if (method === "initialize") {
        write({
          jsonrpc: "2.0",
          id: responseId,
          result: {
            protocolVersion: "2024-11-05",
            serverInfo: { name: "figma-mcp", version: "0.1.0" },
            capabilities: { tools: {} }
          }
        });
      } else if (method === "tools/list") {
        write({ jsonrpc: "2.0", id: responseId, result: { tools } });
      } else if (method === "tools/call") {
        const name = params?.name;
        const args = params?.arguments || {};
        const result = await handleToolCall(name, args);
        write({
          jsonrpc: "2.0",
          id: responseId,
          result: {
            content: [{ type: "text", text: JSON.stringify(result) }]
          }
        });
      } else {
        write({ jsonrpc: "2.0", id: responseId, error: { code: -32601, message: "Method not found" } });
      }
    } catch (e) {
      write({ jsonrpc: "2.0", id: responseId, error: { code: -32000, message: e.message } });
    }
  }
});

process.stdin.on("end", () => process.exit(0));



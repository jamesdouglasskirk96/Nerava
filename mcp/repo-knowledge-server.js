import fs from "node:fs";
import path from "node:path";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const REPO_ROOT = process.env.REPO_ROOT || process.cwd();

// Hard guard: never allow escaping repo root
function resolveInsideRepo(relPath) {
  const abs = path.resolve(REPO_ROOT, relPath);
  const root = path.resolve(REPO_ROOT) + path.sep;
  if (!abs.startsWith(root)) throw new Error("Path escapes REPO_ROOT");
  return abs;
}

const DEFAULT_IGNORES = new Set([
  ".git",
  "node_modules",
  ".next",
  "dist",
  "build",
  ".venv",
  "venv",
  "__pycache__",
  ".pytest_cache",
]);

function shouldIgnore(p) {
  const parts = p.split(path.sep);
  return parts.some((seg) => DEFAULT_IGNORES.has(seg));
}

function walkFiles(dirAbs, out = [], maxFiles = 5000) {
  if (out.length >= maxFiles) return out;
  let entries;
  try {
    entries = fs.readdirSync(dirAbs, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    const abs = path.join(dirAbs, e.name);
    const rel = path.relative(REPO_ROOT, abs);
    if (shouldIgnore(rel)) continue;

    if (e.isDirectory()) {
      walkFiles(abs, out, maxFiles);
      if (out.length >= maxFiles) break;
    } else if (e.isFile()) {
      out.push(rel);
      if (out.length >= maxFiles) break;
    }
  }
  return out;
}

function safeReadText(relPath, maxBytes = 200_000) {
  const abs = resolveInsideRepo(relPath);
  const stat = fs.statSync(abs);
  if (!stat.isFile()) throw new Error("Not a file");
  if (stat.size > maxBytes) throw new Error(`File too large (> ${maxBytes} bytes)`);
  return fs.readFileSync(abs, "utf8");
}

function grepRepo(query, fileGlobs = [], maxMatches = 200) {
  const q = query.toLowerCase();
  const files = walkFiles(path.resolve(REPO_ROOT));
  const filtered = fileGlobs.length
    ? files.filter((f) => fileGlobs.some((g) => f.endsWith(g)))
    : files;

  const matches = [];
  for (const f of filtered) {
    if (matches.length >= maxMatches) break;
    try {
      const text = safeReadText(f);
      const lines = text.split("\n");
      for (let i = 0; i < lines.length; i++) {
        if (matches.length >= maxMatches) break;
        if (lines[i].toLowerCase().includes(q)) {
          matches.push({ file: f, line: i + 1, text: lines[i].slice(0, 300) });
        }
      }
    } catch {
      // ignore unreadable/binary/large files
    }
  }
  return matches;
}

const server = new McpServer({
  name: "repo-knowledge",
  version: "1.0.0",
});

server.tool(
  "repo_info",
  "Return basic repo info and the configured REPO_ROOT.",
  {},
  async () => ({
    content: [{ type: "text", text: `REPO_ROOT=${REPO_ROOT}` }],
  })
);

server.tool(
  "list_files",
  "List repo files (bounded).",
  {
    maxFiles: z.number().int().min(1).max(10000).default(2000),
  },
  async ({ maxFiles }) => {
    const files = walkFiles(path.resolve(REPO_ROOT), [], maxFiles);
    return { content: [{ type: "text", text: files.join("\n") }] };
  }
);

server.tool(
  "read_file",
  "Read a text file inside the repo (bounded).",
  {
    path: z.string().min(1),
  },
  async ({ path: relPath }) => {
    const text = safeReadText(relPath);
    return { content: [{ type: "text", text }] };
  }
);

server.tool(
  "search_repo",
  "Search for a substring across repo files (bounded).",
  {
    query: z.string().min(1),
    fileSuffixes: z.array(z.string()).optional(),
    maxMatches: z.number().int().min(1).max(500).default(200),
  },
  async ({ query, fileSuffixes, maxMatches }) => {
    const matches = grepRepo(query, fileSuffixes ?? [], maxMatches);
    const text =
      matches.length === 0
        ? "No matches."
        : matches
            .map((m) => `${m.file}:${m.line}  ${m.text}`)
            .join("\n");
    return { content: [{ type: "text", text }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("repo-knowledge MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal MCP server error:", err);
  process.exit(1);
});

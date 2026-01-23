import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const SEMGREP_CONFIG = process.env.SEMGREP_CONFIG || "p/owasp-top-ten";
const SCAN_DEPS = process.env.SCAN_DEPS === "true";
const SCAN_SECRETS = process.env.SCAN_SECRETS === "true";

function runCommand(cmd, timeout = 60000) {
  try {
    const result = execSync(cmd, { encoding: "utf8", timeout, maxBuffer: 10 * 1024 * 1024 });
    return result;
  } catch (err) {
    if (err.stdout) return err.stdout;
    return `Error: ${err.message}`;
  }
}

function checkTool(name) {
  try {
    execSync(`which ${name}`, { encoding: "utf8" });
    return true;
  } catch {
    return false;
  }
}

const server = new McpServer({
  name: "security-scanner",
  version: "1.0.0",
});

server.tool(
  "security_info",
  "Return security scanner configuration and available tools.",
  {},
  async () => {
    const tools = {
      semgrep: checkTool("semgrep"),
      bandit: checkTool("bandit"),
      npm_audit: checkTool("npm"),
      pip_audit: checkTool("pip-audit"),
      trivy: checkTool("trivy"),
      gitleaks: checkTool("gitleaks"),
    };
    const available = Object.entries(tools).filter(([_, v]) => v).map(([k]) => k);
    const missing = Object.entries(tools).filter(([_, v]) => !v).map(([k]) => k);
    return {
      content: [{
        type: "text",
        text: `SEMGREP_CONFIG=${SEMGREP_CONFIG}\nSCAN_DEPS=${SCAN_DEPS}\nSCAN_SECRETS=${SCAN_SECRETS}\n\nAvailable: ${available.join(", ") || "none"}\nMissing: ${missing.join(", ") || "none"}`
      }]
    };
  }
);

server.tool(
  "run_semgrep",
  "Run Semgrep security scan on a path.",
  {
    path: z.string().min(1).describe("Path to scan (relative or absolute)"),
    config: z.string().optional().describe("Semgrep config (default: p/owasp-top-ten)"),
  },
  async ({ path: scanPath, config }) => {
    if (!checkTool("semgrep")) {
      return { content: [{ type: "text", text: "Error: semgrep not installed. Run: pip install semgrep" }] };
    }
    const cfg = config || SEMGREP_CONFIG;
    const result = runCommand(`semgrep --config=${cfg} "${scanPath}" --json 2>&1 | head -500`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "run_bandit",
  "Run Bandit Python security scan.",
  {
    path: z.string().min(1).describe("Path to Python files"),
  },
  async ({ path: scanPath }) => {
    if (!checkTool("bandit")) {
      return { content: [{ type: "text", text: "Error: bandit not installed. Run: pip install bandit" }] };
    }
    const result = runCommand(`bandit -r "${scanPath}" -f json 2>&1 | head -500`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "run_npm_audit",
  "Run npm audit on a package directory.",
  {
    path: z.string().min(1).describe("Path to package.json directory"),
  },
  async ({ path: scanPath }) => {
    const result = runCommand(`cd "${scanPath}" && npm audit --json 2>&1 | head -200`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "scan_secrets",
  "Scan for secrets using gitleaks.",
  {
    path: z.string().min(1).describe("Path to scan"),
  },
  async ({ path: scanPath }) => {
    if (!checkTool("gitleaks")) {
      return { content: [{ type: "text", text: "Error: gitleaks not installed. Install from: https://github.com/gitleaks/gitleaks" }] };
    }
    const result = runCommand(`gitleaks detect --source="${scanPath}" --no-git -v 2>&1 | head -100`);
    return { content: [{ type: "text", text: result }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("security-scanner MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal MCP server error:", err);
  process.exit(1);
});

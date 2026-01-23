import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const CI_PROVIDER = process.env.CI_PROVIDER || "github";
const REPO = process.env.REPO || "";

function runCommand(cmd, timeout = 30000) {
  try {
    const result = execSync(cmd, { encoding: "utf8", timeout });
    return result;
  } catch (err) {
    if (err.stdout) return err.stdout;
    return `Error: ${err.message}`;
  }
}

function checkGh() {
  try {
    execSync("which gh", { encoding: "utf8" });
    execSync("gh auth status", { encoding: "utf8", timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

const server = new McpServer({
  name: "ci-gate",
  version: "1.0.0",
});

server.tool(
  "ci_info",
  "Return CI configuration and status.",
  {},
  async () => {
    const ghAuth = checkGh();
    return {
      content: [{
        type: "text",
        text: `CI_PROVIDER=${CI_PROVIDER}\nREPO=${REPO || "(not set)"}\nGitHub CLI authenticated: ${ghAuth}`
      }]
    };
  }
);

server.tool(
  "list_workflows",
  "List GitHub Actions workflows.",
  {
    repo: z.string().optional().describe("Repository (owner/repo)"),
  },
  async ({ repo }) => {
    if (!checkGh()) {
      return { content: [{ type: "text", text: "Error: gh CLI not installed or not authenticated. Run: gh auth login" }] };
    }
    const r = repo || REPO;
    if (!r) {
      return { content: [{ type: "text", text: "Error: No repository specified. Set REPO env var or pass repo parameter." }] };
    }
    const result = runCommand(`gh workflow list --repo ${r} 2>&1`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "list_runs",
  "List recent workflow runs.",
  {
    repo: z.string().optional().describe("Repository (owner/repo)"),
    limit: z.number().optional().describe("Number of runs to show (default: 10)"),
  },
  async ({ repo, limit }) => {
    if (!checkGh()) {
      return { content: [{ type: "text", text: "Error: gh CLI not installed or not authenticated." }] };
    }
    const r = repo || REPO;
    if (!r) {
      return { content: [{ type: "text", text: "Error: No repository specified." }] };
    }
    const l = limit || 10;
    const result = runCommand(`gh run list --repo ${r} --limit ${l} 2>&1`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "get_run",
  "Get details of a specific workflow run.",
  {
    repo: z.string().optional().describe("Repository (owner/repo)"),
    runId: z.string().describe("Workflow run ID"),
  },
  async ({ repo, runId }) => {
    if (!checkGh()) {
      return { content: [{ type: "text", text: "Error: gh CLI not installed or not authenticated." }] };
    }
    const r = repo || REPO;
    if (!r) {
      return { content: [{ type: "text", text: "Error: No repository specified." }] };
    }
    const result = runCommand(`gh run view ${runId} --repo ${r} 2>&1`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "list_prs",
  "List open pull requests.",
  {
    repo: z.string().optional().describe("Repository (owner/repo)"),
  },
  async ({ repo }) => {
    if (!checkGh()) {
      return { content: [{ type: "text", text: "Error: gh CLI not installed or not authenticated." }] };
    }
    const r = repo || REPO;
    if (!r) {
      return { content: [{ type: "text", text: "Error: No repository specified." }] };
    }
    const result = runCommand(`gh pr list --repo ${r} 2>&1`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "get_pr_checks",
  "Get status checks for a pull request.",
  {
    repo: z.string().optional().describe("Repository (owner/repo)"),
    prNumber: z.number().describe("Pull request number"),
  },
  async ({ repo, prNumber }) => {
    if (!checkGh()) {
      return { content: [{ type: "text", text: "Error: gh CLI not installed or not authenticated." }] };
    }
    const r = repo || REPO;
    if (!r) {
      return { content: [{ type: "text", text: "Error: No repository specified." }] };
    }
    const result = runCommand(`gh pr checks ${prNumber} --repo ${r} 2>&1`);
    return { content: [{ type: "text", text: result }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ci-gate MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal MCP server error:", err);
  process.exit(1);
});

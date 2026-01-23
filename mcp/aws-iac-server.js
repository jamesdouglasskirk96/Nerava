import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execSync } from "node:child_process";

const AWS_PROFILE = process.env.AWS_PROFILE || "default";
const AWS_REGION = process.env.AWS_REGION || "us-east-1";

function runAwsCommand(args) {
  try {
    const cmd = `aws --profile ${AWS_PROFILE} --region ${AWS_REGION} ${args}`;
    const result = execSync(cmd, { encoding: "utf8", timeout: 30000 });
    return result;
  } catch (err) {
    return `Error: ${err.message}`;
  }
}

const server = new McpServer({
  name: "aws-iac",
  version: "1.0.0",
});

server.tool(
  "aws_info",
  "Return AWS profile and region configuration.",
  {},
  async () => ({
    content: [{ type: "text", text: `AWS_PROFILE=${AWS_PROFILE}, AWS_REGION=${AWS_REGION}` }],
  })
);

server.tool(
  "aws_sts_identity",
  "Get current AWS caller identity (sts get-caller-identity).",
  {},
  async () => {
    const result = runAwsCommand("sts get-caller-identity --output json");
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "aws_list_stacks",
  "List CloudFormation stacks.",
  {},
  async () => {
    const result = runAwsCommand("cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query 'StackSummaries[].{Name:StackName,Status:StackStatus}' --output table");
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "aws_describe_stack",
  "Describe a CloudFormation stack.",
  {
    stackName: z.string().min(1).describe("Name of the CloudFormation stack"),
  },
  async ({ stackName }) => {
    const result = runAwsCommand(`cloudformation describe-stacks --stack-name "${stackName}" --output json`);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "aws_list_s3_buckets",
  "List S3 buckets.",
  {},
  async () => {
    const result = runAwsCommand("s3 ls");
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "aws_list_ec2_instances",
  "List EC2 instances.",
  {},
  async () => {
    const result = runAwsCommand("ec2 describe-instances --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,Type:InstanceType,Name:Tags[?Key==`Name`].Value|[0]}' --output table");
    return { content: [{ type: "text", text: result }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("aws-iac MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal MCP server error:", err);
  process.exit(1);
});

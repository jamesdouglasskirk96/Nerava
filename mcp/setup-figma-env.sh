#!/bin/bash
# Setup script for Figma MCP environment variables
# Run this script with: source mcp/setup-figma-env.sh
# Or add these exports to your ~/.zshrc

export FIGMA_API_TOKEN=YOUR_FIGMA_API_TOKEN_HERE
export FIGMA_FILE_ID=YOUR_FIGMA_FILE_ID_HERE

echo "✅ Figma MCP environment variables set:"
echo "   FIGMA_API_TOKEN=${FIGMA_API_TOKEN:0:20}..."
echo "   FIGMA_FILE_ID=$FIGMA_FILE_ID"




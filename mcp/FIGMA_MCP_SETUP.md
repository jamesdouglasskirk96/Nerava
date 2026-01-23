# Figma MCP Server Setup

## ✅ Server File Created

The Figma MCP server has been created at:
```
/Users/jameskirk/Desktop/Nerava/mcp/figma-server.js
```

## 📝 MCP Configuration

Update your Cursor MCP configuration (typically in Cursor Settings → MCP) with:

```json
{
  "figma": {
    "command": "node",
    "args": ["/Users/jameskirk/Desktop/Nerava/mcp/figma-server.js"],
    "env": {
      "FIGMA_API_TOKEN": "${FIGMA_API_TOKEN}",
      "FIGMA_FILE_ID": "${FIGMA_FILE_ID}"
    }
  }
}
```

## 🔐 Environment Variables

**✅ Configured:** These have been added to your `~/.zshrc` file:

```bash
export FIGMA_API_TOKEN=YOUR_FIGMA_API_TOKEN_HERE
export FIGMA_FILE_ID=YOUR_FIGMA_FILE_ID_HERE
```

**To activate:** Either:
1. Restart your terminal, or
2. Run: `source ~/.zshrc`

**Alternative:** Use the setup script:
```bash
source mcp/setup-figma-env.sh
```

## 🛠️ Available Tools

The server provides three tools:
1. `figma.get_file` - Fetch full Figma file JSON
2. `figma.get_nodes` - Fetch specific nodes by IDs
3. `figma.get_image_urls` - Get image render URLs for nodes

## 🐛 Troubleshooting

If you see "No server info found" errors, it means the server never launched successfully. Once the file exists and the environment variables are set, restart Cursor and the errors should disappear.


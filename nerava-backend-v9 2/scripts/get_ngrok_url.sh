#!/bin/bash
# Get ngrok URL if it's running

NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    for tunnel in tunnels:
        if tunnel.get('proto') == 'https':
            print(tunnel['public_url'])
            sys.exit(0)
except:
    pass
" 2>/dev/null)

if [ -n "$NGROK_URL" ]; then
    echo "✅ ngrok is running!"
    echo ""
    echo "📱 iPhone Safari URL:"
    echo "   ${NGROK_URL}/v1/wallet/pass/apple/create"
    echo ""
    echo "🔧 Set this as PUBLIC_BASE_URL:"
    echo "   export PUBLIC_BASE_URL=\"${NGROK_URL}\""
else
    echo "❌ ngrok is not running on port 4040"
    echo ""
    echo "To start ngrok:"
    echo "   ngrok http 8000"
    echo ""
    echo "Then run this script again to get the URL"
fi


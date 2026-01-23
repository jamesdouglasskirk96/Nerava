# Fix Port Conflicts

## Quick Fix - Run This:

```bash
# Kill all processes on ports 8001 and 5173
lsof -ti:8001 | xargs kill -9 2>/dev/null; lsof -ti:5173 | xargs kill -9 2>/dev/null; pkill -f "uvicorn app.main" 2>/dev/null; pkill -f vite 2>/dev/null; echo "✅ Ports cleared"
```

## Then Start Servers:

**Terminal 1:**
```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2:**
```bash
cd /Users/jameskirk/Desktop/Nerava/apps/driver
npm run dev
```

## Verify Ports Are Free:

```bash
lsof -i:8001 || echo "Port 8001 is free ✅"
lsof -i:5173 || echo "Port 5173 is free ✅"
```




# Nerava Mobile PWA (browser demo)

## Run
1) Make sure your FastAPI backend is running at http://127.0.0.1:8000
2) Serve this folder statically:
   python3 -m http.server 8080
3) Open http://localhost:8080/index.html

## Point to another backend
Open devtools console and run:
localStorage.setItem("NERAVA_BASE","http://YOUR-IP:8000"); location.reload();

## Defaults
localStorage.setItem("NERAVA_USER","demo@nerava.app");
localStorage.setItem("NERAVA_PREFS","coffee_bakery,quick_bite");

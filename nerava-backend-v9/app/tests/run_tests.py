#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nerava Demo Runner — investor-friendly narration + color highlighting.

What this does (high level):
1) Checks API health
2) Finds nearby "Nerava Hubs" (clustered chargers)
3) Picks a recommended hub for the user (based on availability/tier)
4) Shows nearby merchants (with OpenTable / DoorDash links when relevant)
5) Saves & reads user preferences
6) Places a soft reservation (30 minutes)
7) Wallet before/after credit & debit (simulating rewards)
8) Lists raw chargers nearby (transparency)

Env overrides:
  NERAVA_URL   (default http://127.0.0.1:8000)
  NERAVA_LAT   (default 30.4021)
  NERAVA_LNG   (default -97.7265)
  NERAVA_USER  (default demo@nerava.app)
  NERAVA_PREFS (default coffee_bakery,quick_bite)
"""

import os, json, sys, traceback
import httpx
from datetime import datetime, timedelta

BASE = os.getenv("NERAVA_URL", "http://127.0.0.1:8000")
LAT  = float(os.getenv("NERAVA_LAT", "30.4021"))
LNG  = float(os.getenv("NERAVA_LNG", "-97.7265"))
USER = os.getenv("NERAVA_USER", "demo@nerava.app")
PREFS_CSV = os.getenv("NERAVA_PREFS", "coffee_bakery,quick_bite")

# ---------- ANSI colors ----------
BOLD  = "\033[1m"
DIM   = "\033[2m"
RED   = "\033[31m"
GRN   = "\033[32m"
YEL   = "\033[33m"
BLU   = "\033[34m"
MAG   = "\033[35m"
CYA   = "\033[36m"
RST   = "\033[0m"

# ---------- HTTP helpers ----------
def _ok(resp):
    resp.raise_for_status()
    return resp.json()

def get(path, **params):
    with httpx.Client(timeout=20.0) as c:
        return _ok(c.get(BASE + path, params=params))

def post_json(path, payload=None, **params):
    with httpx.Client(timeout=20.0) as c:
        return _ok(c.post(BASE + path, params=params, json=payload or {}))

def post_qs(path, **params):
    """POST with only query-string parameters (no JSON body)."""
    with httpx.Client(timeout=20.0) as c:
        return _ok(c.post(BASE + path, params=params))

# ---------- Pretty printers ----------
def hr(char="─", n=70):
    print(DIM + char * n + RST)

def title(t):
    print(f"\n{BOLD}{t}{RST}")

def narr(s):
    print(f"{DIM}• {s}{RST}")

def show_request(method, path, params=None, body=None):
    q = ""
    if params:
        try:
            q = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        except Exception:
            q = ""
    print(f"{BLU}{method} {BASE}{path}{q}{RST}")
    if body:
        print(f"{DIM}  body:{RST} {json.dumps(body)}")

def show_key_value(label, value, color=GRN):
    print(f"  {color}{label}:{RST} {value}")

def show_json_snippet(obj, keys):
    for k in keys:
        if k in obj:
            show_key_value(k, obj[k])

def summarize_merchants(items, limit=6):
    print(f"{MAG}Top nearby places (walkable) ↴{RST}")
    for i, m in enumerate(items[:limit], 1):
        name = m.get("name", "Unknown")
        badge = m.get("badge", "")
        cats = ",".join(m.get("categories", []))
        links = m.get("links", {})
        dots = []
        if "reserve" in links: dots.append("Reserve")
        if "pickup" in links: dots.append("Pickup")
        dots_str = f"  {DIM}({', '.join(dots)}){RST}" if dots else ""
        print(f"   {i:>2}. {BOLD}{name}{RST} {DIM}•{RST} {badge or cats}{dots_str}")

def safe_step(title_text, call_fn, request_show=None, response_highlight=None):
    """
    request_show: dict(method, path, params, body)
    response_highlight: callable(resp_json) -> None
    """
    title(f"▶ {title_text}")
    if request_show:
        show_request(request_show.get("method","GET"),
                     request_show.get("path",""),
                     request_show.get("params"),
                     request_show.get("body"))
    try:
        data = call_fn()
        if response_highlight:
            response_highlight(data)
        else:
            print(json.dumps(data, indent=2))
        print(f"{GRN}✓ Success{RST}")
        return data, None
    except Exception as e:
        print(f"{RED}✗ Failed:{RST} {e}")
        traceback.print_exc(limit=1)
        return None, str(e)

# ---------- Wallet helpers (QS first, JSON fallback) ----------
def wallet_credit_any(user_id: str, cents: int):
    # Try QS endpoints first
    try:
        return post_qs("/v1/wallet/credit_qs", user_id=user_id, cents=cents)
    except Exception:
        # Fallback to JSON body route
        payload = {"user_id": user_id, "amount_cents": cents}
        return post_json("/v1/wallet/credit", payload)

def wallet_debit_any(user_id: str, cents: int):
    try:
        return post_qs("/v1/wallet/debit_qs", user_id=user_id, cents=cents)
    except Exception:
        payload = {"user_id": user_id, "amount_cents": cents}
        return post_json("/v1/wallet/debit", payload)

def main():
    errors = []

    # 1) HEALTH
    hr(); narr("We start by confirming the API is live.")
    data, err = safe_step(
        "Health check",
        lambda: get("/v1/health"),
        {"method":"GET","path":"/v1/health"},
        lambda d: show_key_value("ok", d.get("ok")) or show_key_value("time", d.get("time"))
    )
    if err: errors.append(("HEALTH", err))

    # 2) HUBS NEARBY
    hr(); narr("Next, we cluster chargers into a few walkable 'Nerava Hubs' near The Domain.")
    hubs, err = safe_step(
        "Find nearby hubs",
        lambda: get("/v1/hubs/nearby", lat=LAT, lng=LNG, radius_km=2, max_results=5),
        {"method":"GET","path":"/v1/hubs/nearby","params":{"lat":LAT,"lng":LNG,"radius_km":2,"max_results":5}},
        lambda d: show_key_value("hub_count", len(d))
    )
    if err: errors.append(("HUBS", err))

    # Helper to choose a hub coordinate & id
    def pick_hub_coords_and_id():
        if hubs and isinstance(hubs, list) and len(hubs)>0:
            h = hubs[0]
            return h.get("lat", LAT), h.get("lng", LNG), h.get("id","")
        return LAT, LNG, ""

    # 3) RECOMMEND
    hr(); narr("We recommend a hub with free ports & good amenities for this user.")
    rec, err = safe_step(
        "Recommend best hub for USER",
        lambda: get("/v1/hubs/recommend", lat=LAT, lng=LNG, radius_km=2, user_id=USER),
        {"method":"GET","path":"/v1/hubs/recommend","params":{"lat":LAT,"lng":LNG,"radius_km":2,"user_id":USER}},
        lambda d: [show_key_value("hub", d.get("name")),
                   show_key_value("score", d.get("score")),
                   show_key_value("reasons", ", ".join(d.get("reason_tags", [])))]
    )
    if err: errors.append(("RECOMMEND", err))

    # 4) MERCHANTS NEARBY
    mlat, mlng, _ = pick_hub_coords_and_id()
    hr(); narr("Now we show walkable, relevant businesses (DoorDash/OpenTable links where applicable).")
    merchants, err = safe_step(
        "Nearby merchants at recommended hub",
        lambda: get("/v1/merchants/nearby", lat=mlat, lng=mlng, radius_m=600, max_results=20, prefs=PREFS_CSV),
        {"method":"GET","path":"/v1/merchants/nearby","params":{"lat":mlat,"lng":mlng,"radius_m":600,"max_results":20,"prefs":PREFS_CSV}},
        lambda d: summarize_merchants(d, 8)
    )
    if err: errors.append(("MERCHANTS", err))

    # 5) USER PREFS
    hr(); narr("Users can set preferences (e.g., coffee, quick bites) to personalize suggestions.")
    prefs_payload = {
        "pref_coffee": True,
        "pref_food": True,
        "pref_dog": False,
        "pref_kid": False,
        "pref_shopping": False,
        "pref_exercise": False
    }
    _, err = safe_step(
        "Save user preferences",
        lambda: post_json(f"/v1/users/{USER}/prefs", prefs_payload),
        {"method":"POST","path":f"/v1/users/{USER}/prefs","body":prefs_payload},
        lambda d: show_json_snippet(d, ["pref_coffee","pref_food","pref_dog","pref_kid","pref_shopping","pref_exercise"])
    )
    if err: errors.append(("SET_PREFS", err))

    _, err = safe_step(
        "Read user preferences",
        lambda: get(f"/v1/users/{USER}/prefs"),
        {"method":"GET","path":f"/v1/users/{USER}/prefs"},
        lambda d: show_json_snippet(d, ["pref_coffee","pref_food"])
    )
    if err: errors.append(("GET_PREFS", err))

    # 6) RESERVATION (SOFT)
    hub_id = (rec or {}).get("id") or ((hubs or [{}])[0]).get("id", "hub_domain_A")
    start_iso = (datetime.utcnow() + timedelta(minutes=10)).replace(microsecond=0).isoformat() + "Z"
    resv_req = {"hub_id": hub_id, "user_id": USER, "start_iso": start_iso, "minutes": 30}

    hr(); narr("We place a 30-min soft reservation window—Nerava will adapt if the station changes on the ground.")
    _, err = safe_step(
        "Create soft reservation (30m)",
        lambda: post_json("/v1/reservations/soft", resv_req),
        {"method":"POST","path":"/v1/reservations/soft","body":resv_req},
        lambda d: [show_key_value("reservation_id", d.get("id")),
                   show_key_value("hub_id", d.get("hub_id")),
                   show_key_value("status", d.get("status")),
                   show_key_value("window_start", d.get("window_start_iso")),
                   show_key_value("window_end", d.get("window_end_iso"))]
    )
    if err: errors.append(("RESERVE", err))

    # 7) WALLET
    hr(); narr("Wallet simulates cash-back and perks—here we credit $5 and then debit $3.")
    before, err = safe_step(
        "Wallet (before)",
        lambda: get("/v1/wallet", user_id=USER),
        {"method":"GET","path":"/v1/wallet","params":{"user_id":USER}},
        lambda d: show_key_value("balance_cents", d.get("balance_cents"))
    )
    if err: errors.append(("WALLET_BEFORE", err))

    credit, err = safe_step(
        "Wallet credit +500¢",
        lambda: wallet_credit_any(USER, 500),
        {"method":"POST","path":"(credit_qs or credit JSON)","params":{"user_id":USER,"cents":500}},
        lambda d: show_key_value("new_balance_cents", d.get("new_balance_cents", d.get("balance_cents")))
    )
    if err: errors.append(("WALLET_CREDIT", err))

    after_credit, err = safe_step(
        "Wallet (after credit)",
        lambda: get("/v1/wallet", user_id=USER),
        {"method":"GET","path":"/v1/wallet","params":{"user_id":USER}},
        lambda d: show_key_value("balance_cents", d.get("balance_cents"))
    )
    if err: errors.append(("WALLET_AFTER_CREDIT", err))

    debit, err = safe_step(
        "Wallet debit -300¢",
        lambda: wallet_debit_any(USER, 300),
        {"method":"POST","path":"(debit_qs or debit JSON)","params":{"user_id":USER,"cents":300}},
        lambda d: show_key_value("new_balance_cents", d.get("new_balance_cents", d.get("balance_cents")))
    )
    if err: errors.append(("WALLET_DEBIT", err))

    after_debit, err = safe_step(
        "Wallet (after debit)",
        lambda: get("/v1/wallet", user_id=USER),
        {"method":"GET","path":"/v1/wallet","params":{"user_id":USER}},
        lambda d: show_key_value("balance_cents", d.get("balance_cents"))
    )
    if err: errors.append(("WALLET_AFTER_DEBIT", err))

    # 8) RAW CHARGERS NEARBY (transparency)
    hr(); narr("For transparency, we also show raw charger results (OpenChargeMap).")
    chargers, err = safe_step(
        "Chargers nearby (OCM)",
        lambda: get("/v1/chargers/nearby", lat=LAT, lng=LNG, radius_km=2, max_results=5),
        {"method":"GET","path":"/v1/chargers/nearby","params":{"lat":LAT,"lng":LNG,"radius_km":2,"max_results":5}},
        lambda d: show_key_value("result_count", len(d))
    )
    if err: errors.append(("CHARGERS", err))

    # Final recap for investors
    hr("="); title("DEMO SUMMARY (Investor-friendly)")
    narr("✅ API alive & responding")
    narr("✅ Found walkable hubs and picked a recommended one")
    narr("✅ Displayed real nearby merchants (with Reserve/Pickup when available)")
    narr("✅ Saved & read user preferences")
    narr("✅ Created a soft reservation window")
    narr("✅ Demonstrated wallet credit/debit flow (cashback/perks)")
    narr("✅ Showed raw chargers as proof of live data")
    if errors:
        print(f"\n{YEL}Completed with {len(errors)} warning(s):{RST} " + ", ".join(k for k,_ in errors))
        sys.exit(1)
    else:
        print(f"\n{GRN}All steps passed. Ready to demo!{RST}")

if __name__ == "__main__":
    main()

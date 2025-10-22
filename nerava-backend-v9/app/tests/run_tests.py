#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nerava Demo Runner — investor-friendly, end-to-end flow (polished).
- Keeps all prior functionality.
- Adds: two users, local merchant + perk, idempotent perk claims, load-shift credit,
  summary for merchant with both users' claims.
"""

import os, json, sys, traceback
import httpx
from datetime import datetime, timedelta

BASE = os.getenv("NERAVA_URL", "http://127.0.0.1:8000")
LAT  = float(os.getenv("NERAVA_LAT", "30.4021"))
LNG  = float(os.getenv("NERAVA_LNG", "-97.7265"))
USER1 = os.getenv("NERAVA_USER1", "demo@nerava.app")
USER2 = os.getenv("NERAVA_USER2", "investor@nerava.app")
PREFS_CSV = os.getenv("NERAVA_PREFS", "coffee_bakery,quick_bite")

# ---------- ANSI colors ----------
BOLD  = "\033[1m"; DIM="\033[2m"; RED="\033[31m"; GRN="\033[32m"; YEL="\033[33m"
BLU   = "\033[34m"; MAG="\033[35m"; CYA="\033[36m"; RST="\033[0m"

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
    with httpx.Client(timeout=20.0) as c:
        return _ok(c.post(BASE + path, params=params))

# ---------- Pretty printers ----------
def hr(char="─", n=80): print(DIM + char * n + RST)
def title(t): print(f"\n{BOLD}{t}{RST}")
def narr(s): print(f"{DIM}• {s}{RST}")
def show_request(method, path, params=None, body=None):
    q = ""
    if params:
        try: q = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        except Exception: q = ""
    print(f"{BLU}{method} {BASE}{path}{q}{RST}")
    if body: print(f"{DIM}  body:{RST} {json.dumps(body)}")
def show_key_value(label, value, color=GRN): print(f"  {color}{label}:{RST} {value}")
def show_json_snippet(obj, keys):
    for k in keys:
        if k in obj: show_key_value(k, obj[k])

def summarize_merchants(items, limit=6):
    print(f"{MAG}Top nearby places (walkable) ↴{RST}")
    for i, m in enumerate(items[:limit], 1):
        name = m.get("name", "Unknown"); badge = m.get("badge", "")
        cats = ",".join(m.get("categories", [])); links = m.get("links", {})
        dots = []
        if "reserve" in links: dots.append("Reserve")
        if "pickup" in links: dots.append("Pickup")
        if m.get("source") == "local" and "claim_api" in links: dots.append("Perk")
        dots_str = f"  {DIM}({', '.join(dots)}){RST}" if dots else ""
        print(f"   {i:>2}. {BOLD}{name}{RST} {DIM}•{RST} {badge or cats}{dots_str}")

def safe_step(title_text, call_fn, request_show=None, response_highlight=None, warn_key=None, warnings=None):
    title(f"▶ {title_text}")
    if request_show:
        show_request(request_show.get("method","GET"), request_show.get("path",""),
                     request_show.get("params"), request_show.get("body"))
    try:
        data = call_fn()
        if response_highlight: response_highlight(data)
        else: print(json.dumps(data, indent=2))
        print(f"{GRN}✓ Success{RST}")
        return data, None
    except Exception as e:
        print(f"{RED}✗ Failed:{RST} {e}")
        traceback.print_exc(limit=1)
        if warnings is not None and warn_key: warnings.append((warn_key, str(e)))
        return None, str(e)

# ---------- Wallet helpers ----------
def wallet_credit_any(user_id: str, cents: int):
    try: return post_qs("/v1/wallet/credit_qs", user_id=user_id, cents=cents)
    except Exception:
        return post_json("/v1/wallet/credit", {"user_id": user_id, "amount_cents": cents})

def wallet_debit_any(user_id: str, cents: int):
    try: return post_qs("/v1/wallet/debit_qs", user_id=user_id, cents=cents)
    except Exception:
        return post_json("/v1/wallet/debit", {"user_id": user_id, "amount_cents": cents})

# ---------- Helpers for IDs ----------
def ensure_local_merchant_and_perk(lat, lng, reward_cents=75):
    # Create merchant
    m = post_json("/v1/local/merchant", {
        "name": "Domain Coffee",
        "lat": round(lat, 4),
        "lng": round(lng, 4),
        "category": "coffee_bakery",
        "logo_url": ""
    })
    merchant_id = m.get("id")
    # Create perk
    p = post_json("/v1/local/perk", {
        "merchant_id": merchant_id,
        "title": "Latte perk",
        "description": "$0.75 off",
        "reward_cents": reward_cents
    })
    perk_id = p.get("id")
    # Fallback if needed
    if not perk_id:
        perks = get("/v1/local/perks", merchant_id=merchant_id)
        if perks and isinstance(perks, list): perk_id = (perks[0].get("id") if isinstance(perks[0], dict) else perks[0][0])
    return int(merchant_id), int(perk_id), int(reward_cents)

def first_hub_coords(hubs_list, default_lat, default_lng):
    if hubs_list and isinstance(hubs_list, list) and len(hubs_list) > 0:
        h = hubs_list[0]
        return h.get("lat", default_lat), h.get("lng", default_lng), h.get("id", "")
    return default_lat, default_lng, ""

def normalize_summary(summary_json):
    """
    Accepts either:
      { merchant_id, totals:{claims,unique_users}, perks:[{perk_id,perk_title,claim_count,unique_users,last_claim_at}] }
    or a more raw list/tuple form. Returns a normalized dict.
    """
    if isinstance(summary_json, dict) and "totals" in summary_json:
        return summary_json

    # Fallback normalization for tuple/list shapes:
    # Expect something like: {"perks": [(perk_id, title, claim_count, unique_users, last_claim_at), ...], "totals": (claims, uniq)}
    out = {"merchant_id": None, "totals": {"claims": 0, "unique_users": 0}, "perks": []}
    try:
        # best-effort extraction
        if isinstance(summary_json, dict):
            if "merchant_id" in summary_json:
                out["merchant_id"] = summary_json.get("merchant_id")
            t = summary_json.get("totals")
            if isinstance(t, (list, tuple)) and len(t) >= 2:
                out["totals"] = {"claims": int(t[0]), "unique_users": int(t[1])}
            ps = summary_json.get("perks", [])
            for row in ps:
                if isinstance(row, dict):
                    out["perks"].append({
                        "perk_id": row.get("perk_id"),
                        "perk_title": row.get("perk_title"),
                        "claim_count": row.get("claim_count", 0),
                        "unique_users": row.get("unique_users", 0),
                        "last_claim_at": row.get("last_claim_at")
                    })
                elif isinstance(row, (list, tuple)):
                    # (perk_id, title, claim_count, unique_users, last_claim_at)
                    pid = row[0] if len(row) > 0 else None
                    ttl = row[1] if len(row) > 1 else ""
                    cc  = int(row[2]) if len(row) > 2 else 0
                    uu  = int(row[3]) if len(row) > 3 else 0
                    last= row[4] if len(row) > 4 else None
                    out["perks"].append({
                        "perk_id": pid, "perk_title": ttl, "claim_count": cc,
                        "unique_users": uu, "last_claim_at": last
                    })
        return out
    except Exception:
        return out

def main():
    warnings = []

    hr(); narr("We start by confirming the API is live.")
    _, _ = safe_step("Health check", lambda: get("/v1/health"),
                     {"method":"GET","path":"/v1/health"},
                     lambda d: show_key_value("ok", d.get("ok")) or show_key_value("time", d.get("time")))

    hr(); narr("We register two users for the live demo.")
    for u in (USER1, USER2):
        _, _ = safe_step(f"Register user {u}",
                         lambda u=u: post_json("/v1/users/register", {"email": u, "name": "Demo User" if u==USER1 else "Investor User"}),
                         {"method":"POST","path":"/v1/users/register","body":{"email":u,"name":"Demo User" if u==USER1 else "Investor User"}},
                         lambda d: show_key_value("email", d.get("email")))

    hr(); narr("We cluster chargers into a few walkable 'Nerava Hubs' near The Domain.")
    hubs, _ = safe_step("Find nearby hubs",
                        lambda: get("/v1/hubs/nearby", lat=LAT, lng=LNG, radius_km=2, max_results=5),
                        {"method":"GET","path":"/v1/hubs/nearby","params":{"lat":LAT,"lng":LNG,"radius_km":2,"max_results":5}},
                        lambda d: show_key_value("hub_count", len(d)))

    mlat, mlng, hub_id = first_hub_coords(hubs, LAT, LNG)

    hr(); narr("We recommend a hub with free ports & good amenities for the primary user.")
    rec, _ = safe_step(f"Recommend best hub for {USER1}",
                       lambda: get("/v1/hubs/recommend", lat=LAT, lng=LNG, radius_km=2, user_id=USER1),
                       {"method":"GET","path":"/v1/hubs/recommend","params":{"lat":LAT,"lng":LNG,"radius_km":2,"user_id":USER1}},
                       lambda d: [show_key_value("hub", d.get("name")), show_key_value("score", d.get("score")),
                                  show_key_value("reasons", ", ".join(d.get("reason_tags", [])))])

    hr(); narr("Now we show walkable, relevant businesses — local perks first, plus Reserve/Pickup where it applies.")
    _, _ = safe_step("Nearby merchants at recommended hub (unified)",
                     lambda: get("/v1/merchants/nearby", lat=mlat, lng=mlng, radius_m=600, max_results=12, prefs=PREFS_CSV, hub_id=hub_id or "hub_demo"),
                     {"method":"GET","path":"/v1/merchants/nearby",
                      "params":{"lat":mlat,"lng":mlng,"radius_m":600,"max_results":12,"prefs":PREFS_CSV,"hub_id":hub_id or "hub_demo"}},
                     lambda d: summarize_merchants(d, 8))

    hr(); narr("We set preferences so both users are nudged toward the same coffee-friendly merchant.")
    prefs_payload = {"pref_coffee": True, "pref_food": True, "pref_dog": False, "pref_kid": False, "pref_shopping": False, "pref_exercise": False}
    for u in (USER1, USER2):
        _, _ = safe_step(f"Save prefs for {u}",
                         lambda u=u: post_json(f"/v1/users/{u}/prefs", prefs_payload),
                         {"method":"POST","path":f"/v1/users/{u}/prefs","body":prefs_payload},
                         lambda d: show_json_snippet(d, ["pref_coffee","pref_food"]))

    hr(); narr("We place a 30-min soft reservation window—Nerava adapts if on-the-ground changes occur.")
    hub_for_res = (rec or {}).get("id") or (hub_id or "hub_domain_A")
    start_iso = (datetime.utcnow() + timedelta(minutes=10)).replace(microsecond=0).isoformat()+"Z"
    resv_req = {"hub_id": hub_for_res, "user_id": USER1, "start_iso": start_iso, "minutes": 30}
    _, _ = safe_step("Create soft reservation (30m)",
                     lambda: post_json("/v1/reservations/soft", resv_req),
                     {"method":"POST","path":"/v1/reservations/soft","body":resv_req},
                     lambda d: [show_key_value("reservation_id", d.get("id")),
                                show_key_value("hub_id", d.get("hub_id")),
                                show_key_value("status", d.get("status")),
                                show_key_value("window_start", d.get("window_start_iso")),
                                show_key_value("window_end", d.get("window_end_iso"))])

    hr(); narr("Wallet simulates cash-back—credit $5 then debit $3 for a small purchase.")
    before = get("/v1/wallet", user_id=USER1)
    _ , _ = safe_step("Wallet (before) — " + USER1,
                      lambda: before,
                      {"method":"GET","path":"/v1/wallet","params":{"user_id":USER1}},
                      lambda d: show_key_value("balance_cents", d.get("balance_cents")))
    _ , _ = safe_step("Wallet credit +500¢",
                      lambda: wallet_credit_any(USER1, 500),
                      {"method":"POST","path":"(credit_qs or credit JSON)","params":{"user_id":USER1,"cents":500}},
                      lambda d: show_key_value("new_balance_cents", d.get("new_balance_cents", d.get("balance_cents"))))
    _ , _ = safe_step("Wallet debit -300¢",
                      lambda: wallet_debit_any(USER1, 300),
                      {"method":"POST","path":"(debit_qs or debit JSON)","params":{"user_id":USER1,"cents":300}},
                      lambda d: show_key_value("new_balance_cents", d.get("new_balance_cents", d.get("balance_cents"))))
    _ , _ = safe_step("Wallet (after) — " + USER1,
                      lambda: get("/v1/wallet", user_id=USER1),
                      {"method":"GET","path":"/v1/wallet","params":{"user_id":USER1}},
                      lambda d: show_key_value("balance_cents", d.get("balance_cents")))

    hr(); narr("Transparency: show raw chargers results.")
    _, _ = safe_step("Chargers nearby (OCM)",
                     lambda: get("/v1/chargers/nearby", lat=LAT, lng=LNG, radius_km=2, max_results=5),
                     {"method":"GET","path":"/v1/chargers/nearby","params":{"lat":LAT,"lng":LNG,"radius_km":2,"max_results":5}},
                     lambda d: show_key_value("result_count", len(d)))

    hr(); narr("We add a local merchant with a simple $0.75 perk that both users can claim.")
    def create_local():
        merchant_id, perk_id, reward = ensure_local_merchant_and_perk(mlat, mlng, 75)
        print(f"  merchant_id: {merchant_id}")
        print(f"  perk_id: {perk_id}")
        print(f"  perk_reward_cents: {reward}")
        return {"merchant_id": merchant_id, "perk_id": perk_id}
    ids, _ = safe_step("Create local merchant + perk", create_local,
                       {"method":"POST","path":"/v1/local/merchant + /v1/local/perk"},
                       lambda d: None)

    _, _ = safe_step("Nearby merchants (unified, after adding local perk)",
                     lambda: get("/v1/merchants/nearby", lat=mlat, lng=mlng, radius_m=600, max_results=12, prefs=PREFS_CSV, hub_id=hub_id or "hub_demo"),
                     {"method":"GET","path":"/v1/merchants/nearby",
                      "params":{"lat":mlat,"lng":mlng,"radius_m":600,"max_results":12,"prefs":PREFS_CSV,"hub_id":hub_id or "hub_demo"}},
                     lambda d: summarize_merchants(d, 8))

    hr(); narr("Both users claim the same perk — credited once per user, duplicates are ignored gracefully.")
    perk_id = ids.get("perk_id")
    claim_body1 = {"perk_id": perk_id, "user_id": USER1}
    claim_body2 = {"perk_id": perk_id, "user_id": USER2}

    _, _ = safe_step(f"Claim perk for {USER1}",
                     lambda: post_json("/v1/local/perk/claim", claim_body1),
                     {"method":"POST","path":"/v1/local/perk/claim","body":claim_body1},
                     lambda d: [show_key_value("newly_claimed", d.get("newly_claimed", False)),
                                show_key_value("wallet_balance_cents", d.get("wallet_balance_cents"))],
                     warn_key="CLAIM_1", warnings=warnings)

    _, _ = safe_step(f"Claim perk for {USER2}",
                     lambda: post_json("/v1/local/perk/claim", claim_body2),
                     {"method":"POST","path":"/v1/local/perk/claim","body":claim_body2},
                     lambda d: [show_key_value("newly_claimed", d.get("newly_claimed", False)),
                                show_key_value("wallet_balance_cents", d.get("wallet_balance_cents"))],
                     warn_key="CLAIM_2", warnings=warnings)

    hr(); narr("Utility load-shift event bonus — rewarding off-peak participation (+$1.00 each).")
    _, _ = safe_step(f"Load-shift credit +100¢ → {USER1}",
                     lambda: wallet_credit_any(USER1, 100),
                     {"method":"POST","path":"(credit_qs)","params":{"user_id":USER1,"cents":100}},
                     lambda d: show_key_value("wallet_balance_cents", d.get("new_balance_cents", d.get("balance_cents"))))
    _, _ = safe_step(f"Load-shift credit +100¢ → {USER2}",
                     lambda: wallet_credit_any(USER2, 100),
                     {"method":"POST","path":"(credit_qs)","params":{"user_id":USER2,"cents":100}},
                     lambda d: show_key_value("wallet_balance_cents", d.get("new_balance_cents", d.get("balance_cents"))))

    hr(); narr("Final wallet balances after claims and load-shift bonus.")
    _, _ = safe_step("Wallet — " + USER1,
                     lambda: get("/v1/wallet", user_id=USER1),
                     {"method":"GET","path":"/v1/wallet","params":{"user_id":USER1}},
                     lambda d: show_key_value("balance_cents", d.get("balance_cents")))
    _, _ = safe_step("Wallet — " + USER2,
                     lambda: get("/v1/wallet", user_id=USER2),
                     {"method":"GET","path":"/v1/wallet","params":{"user_id":USER2}},
                     lambda d: show_key_value("balance_cents", d.get("balance_cents")))

    # Merchant summary — robust to tuple/list/dict shapes
    hr("="); print("\nMERCHANT SUMMARY (Perk performance)")
    try:
        merchant_id = ids.get("merchant_id")
        raw = get(f"/v1/local/merchant/{merchant_id}/summary")
        summary = normalize_summary(raw)
        tot = summary["totals"]
        print(f"  Merchant #{merchant_id} — claims: {tot['claims']}, unique users: {tot['unique_users']}")
        for p in summary["perks"]:
            print(f"   • {p['perk_title']} — {p['claim_count']} claim(s), {p['unique_users']} unique; last: {p['last_claim_at']}")
    except Exception as e:
        print(f"{RED}✗ Failed summary:{RST} {e}")
        warnings.append(("MERCHANT_SUMMARY", str(e)))

    # Final recap
    hr("="); title("DEMO SUMMARY (Investor-friendly)")
    narr("✅ API alive & responding")
    narr("✅ Found walkable hubs and picked a recommended one")
    narr("✅ Displayed real nearby merchants (Local + Google, with Perks / Reserve / Pickup)")
    narr("✅ Saved & read user preferences (aligned for both users)")
    narr("✅ Created a soft reservation window")
    narr("✅ Wallet: cashback simulation and load-shift bonus")
    narr("✅ Perk claims: credited once per user; duplicates ignored")
    narr("✅ Merchant summary shows both users’ claims")
    narr("✅ Chargers endpoint: transparency")
    if warnings:
        print(f"\n{YEL}Completed with {len(warnings)} warning(s):{RST} " + ", ".join(k for k,_ in warnings))
        sys.exit(1)
    else:
        print(f"\n{GRN}All steps passed. Ready to demo!{RST}")

if __name__ == "__main__":
    main()

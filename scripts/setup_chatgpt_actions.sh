#!/usr/bin/env bash
set -euo pipefail

# Setup Nerava API for ChatGPT Actions via Cloudflare Tunnel

BOLD="\033[1m"; GREEN="\033[32m"; CYAN="\033[36m"; RESET="\033[0m"
step() { printf "\n${BOLD}${CYAN}▶ $1${RESET}\n"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$1"; }

cd nerava-backend-v9 || { echo "❌ Must run from repo root"; exit 1; }

# Start API in background
step "Starting Nerava API on port 8001"
source .venv/bin/activate
python3 -m alembic upgrade head > /dev/null 2>&1 || true

# Kill any existing server on 8001
if lsof -ti tcp:8001 >/dev/null 2>&1; then
  kill -9 "$(lsof -ti tcp:8001)" || true
fi

uvicorn app.main_simple:app --port 8001 --reload > /tmp/nerava_api.log 2>&1 &
API_PID=$!
echo "API process: $API_PID"

# Wait for server to be ready
sleep 3
if ! curl -fsS http://localhost:8001/health >/dev/null 2>&1; then
  echo "❌ API failed to start"
  exit 1
fi
ok "API is running"

# Start Cloudflare Tunnel
step "Starting Cloudflare Tunnel"
cloudflared tunnel --url http://127.0.0.1:8001 > /tmp/cloudflare_tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "Tunnel process: $TUNNEL_PID"

# Wait for tunnel URL
sleep 5
TUNNEL_URL=$(grep -Eo 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cloudflare_tunnel.log | grep -v 'api.trycloudflare.com' | head -n1)

if [ -z "$TUNNEL_URL" ]; then
  echo "❌ Failed to get tunnel URL"
  exit 1
fi

ok "Tunnel URL: $TUNNEL_URL"

# Create OpenAPI spec file
step "Generating OpenAPI spec for ChatGPT Actions"
cat > openapi-actions.yaml <<'EOF'
openapi: 3.1.0
info:
  title: Nerava Actions API
  version: "2025-10-29"
  description: >
    GPT-first API for Nerava: Find → Verify → Earn → Spend → Share.
    Includes charger & merchant discovery, session verification, events, and community pool.

servers:
  - url: $TUNNEL_URL
    description: Cloudflare tunnel (demo)
  - url: http://localhost:8001
    description: Local development

security:
  - ApiKeyAuth: []

paths:
  /health:
    get:
      operationId: health
      summary: Health check
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthRes'

  /v1/gpt/find_charger:
    get:
      operationId: findCharger
      summary: Find EV chargers near a point
      parameters:
        - in: query
          name: lat
          required: true
          schema: { type: number }
        - in: query
          name: lng
          required: true
          schema: { type: number }
        - in: query
          name: radius_m
          required: false
          schema: { type: integer, default: 3000, minimum: 50, maximum: 20000 }
        - in: query
          name: city
          required: false
          schema: { type: string }
      responses:
        "200":
          description: List of chargers or an empty-state hint
          content:
            application/json:
              schema:
                oneOf:
                  - type: array
                    items: { $ref: '#/components/schemas/Charger' }
                  - $ref: '#/components/schemas/HintResponse'

  /v1/gpt/find_merchants:
    get:
      operationId: findMerchants
      summary: Find merchants near a point (optional category)
      parameters:
        - in: query
          name: lat
          required: true
          schema: { type: number }
        - in: query
          name: lng
          required: true
          schema: { type: number }
        - in: query
          name: category
          required: false
          schema: { type: string, enum: [coffee, gym, qsr, wellness, other] }
        - in: query
          name: radius_m
          required: false
          schema: { type: integer, default: 1200, minimum: 50, maximum: 20000 }
      responses:
        "200":
          description: List of merchants or an empty-state hint
          content:
            application/json:
              schema:
                oneOf:
                  - type: array
                    items: { $ref: '#/components/schemas/Merchant' }
                  - $ref: '#/components/schemas/HintResponse'

  /v1/gpt/create_session_link:
    post:
      operationId: createSessionLink
      summary: Create a public verify URL (short-lived JWT)
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateSessionLinkReq' }
      responses:
        "200":
          description: Verify link created
          content:
            application/json:
              schema: { $ref: '#/components/schemas/CreateSessionLinkRes' }

  /v1/sessions/locate:
    post:
      operationId: locate
      summary: Complete verification by posting device GPS
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/LocateReq' }
      responses:
        "200":
          description: Verification result (includes friendly message)
          content:
            application/json:
              schema: { $ref: '#/components/schemas/LocateRes' }

  /v1/gpt/me:
    get:
      operationId: me
      summary: User wallet + stats snapshot
      parameters:
        - in: query
          name: user_id
          required: true
          schema: { type: integer, minimum: 1 }
      responses:
        "200":
          description: User snapshot
          content:
            application/json:
              schema: { $ref: '#/components/schemas/MeRes' }

  /v1/events:
    post:
      operationId: createEvent
      summary: Create an event (activator)
      parameters:
        - in: header
          name: X-User-Id
          required: true
          schema: { type: integer, minimum: 1 }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/EventCreate' }
      responses:
        "200":
          description: Event created
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Event' }

  /v1/events/nearby:
    get:
      operationId: eventsNearby
      summary: List events near a point
      parameters:
        - in: query
          name: lat
          required: true
          schema: { type: number }
        - in: query
          name: lng
          required: true
          schema: { type: number }
        - in: query
          name: radius_m
          required: false
          schema: { type: integer, default: 2000, minimum: 50, maximum: 20000 }
        - in: query
          name: now
          required: false
          schema: { type: string, format: date-time }
      responses:
        "200":
          description: Nearby events (sorted by distance then start time)
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/EventNearby' }

  /v1/events/{event_id}/join:
    post:
      operationId: joinEvent
      summary: Join an event
      parameters:
        - in: path
          name: event_id
          required: true
          schema: { type: integer }
        - in: header
          name: X-User-Id
          required: true
          schema: { type: integer, minimum: 1 }
      responses:
        "200":
          description: Joined
          content:
            application/json:
              schema: { $ref: '#/components/schemas/EventJoinRes' }

  /v1/events/{event_id}/verify/start:
    post:
      operationId: startEventVerification
      summary: Start event verification
      parameters:
        - in: path
          name: event_id
          required: true
          schema: { type: integer }
        - in: header
          name: X-User-Id
          required: true
          schema: { type: integer, minimum: 1 }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/VerificationStartReq' }
      responses:
        "200":
          description: Verification started
          content:
            application/json:
              schema: { $ref: '#/components/schemas/VerificationStartRes' }

  /v1/events/verify/{verification_id}/complete:
    post:
      operationId: completeEventVerification
      summary: Complete event verification (geo / optional photo/QR)
      parameters:
        - in: path
          name: verification_id
          required: true
          schema: { type: string }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/VerificationCompleteReq' }
      responses:
        "200":
          description: Verification result
          content:
            application/json:
              schema: { $ref: '#/components/schemas/VerificationCompleteRes' }

  /v1/pool/summary:
    get:
      operationId: poolSummary
      summary: City community pool summary
      parameters:
        - in: query
          name: city
          required: true
          schema: { type: string }
        - in: query
          name: range
          required: false
          schema: { type: string, enum: [today, 7d, 30d], default: 7d }
      responses:
        "200":
          description: Pool summary
          content:
            application/json:
              schema: { $ref: '#/components/schemas/PoolSummaryRes' }

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-Api-Key

  schemas:
    HealthRes:
      type: object
      properties:
        ok: { type: boolean }
      required: [ok]

    HintResponse:
      type: object
      properties:
        items:
          type: array
          items: {}
          description: Always empty when hint is present
        hint:
          type: object
          properties:
            suggestions:
              type: array
              items: { type: string }
            next_steps:
              type: string
          required: [suggestions, next_steps]
      required: [items, hint]

    Charger:
      type: object
      properties:
        charger_id: { oneOf: [ { type: string }, { type: integer } ] }
        name: { type: string }
        lat: { type: number }
        lng: { type: number }
        network: { type: string }
        distance_m: { type: number }
        green_window:
          type: object
          properties:
            start: { type: string, pattern: "^[0-2][0-9]:[0-5][0-9]$" }
            end:   { type: string, pattern: "^[0-2][0-9]:[0-5][0-9]$" }
          required: [start, end]
        nearby_merchants:
          type: array
          items:
            type: object
            properties:
              merchant_id: { type: integer }
              name: { type: string }
              category: { type: string }
              distance_m: { type: number }
            required: [merchant_id, name, category, distance_m]
      required: [charger_id, name, lat, lng, network, distance_m, green_window, nearby_merchants]

    Merchant:
      type: object
      properties:
        merchant_id: { type: integer }
        name: { type: string }
        category: { type: string }
        lat: { type: number }
        lng: { type: number }
        distance_m: { type: number }
        has_offer: { type: boolean }
        offer:
          nullable: true
          type: object
          properties:
            title: { type: string }
            window_start: { type: string, pattern: "^[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$" }
            window_end:   { type: string, pattern: "^[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$" }
            est_reward_cents: { type: integer }
            source: { type: string, enum: [local, affiliate, square] }
          required: [title, window_start, window_end, est_reward_cents]
      required: [merchant_id, name, category, lat, lng, distance_m, has_offer]

    CreateSessionLinkReq:
      type: object
      properties:
        user_id: { type: integer, minimum: 1 }
        lat: { type: number, nullable: true }
        lng: { type: number, nullable: true }
        charger_hint: { oneOf: [ { type: string }, { type: integer }, { type: 'null' } ] }
      required: [user_id]

    CreateSessionLinkRes:
      type: object
      properties:
        session_id: { oneOf: [ { type: string }, { type: integer } ] }
        url: { type: string }
        expires_at: { type: string, format: date-time }
      required: [session_id, url, expires_at]

    LocateReq:
      type: object
      properties:
        ts: { type: string, format: date-time }
        lat: { type: number }
        lng: { type: number }
        accuracy: { type: number }
        ua: { type: string }
      required: [ts, lat, lng, accuracy]

    LocateRes:
      type: object
      properties:
        verified: { type: boolean }
        status: { type: string }
        reason: { type: string, nullable: true }
        wallet_delta_cents: { type: integer, nullable: true }
        message: { type: string, nullable: true }
      required: [verified, status]

    MeRes:
      type: object
      properties:
        handle: { type: string }
        reputation: { type: integer }
        followers: { type: integer }
        following: { type: integer }
        wallet_cents: { type: integer }
        month_self_cents: { type: integer }
        month_pool_cents: { type: integer }
      required: [handle, reputation, followers, following, wallet_cents, month_self_cents, month_pool_cents]

    EventCreate:
      type: object
      properties:
        title: { type: string }
        description: { type: string }
        category: { type: string }
        city: { type: string }
        lat: { type: number }
        lng: { type: number }
        starts_at: { type: string, format: date-time }
        ends_at: { type: string, format: date-time }
        green_window_start: { type: string, pattern: "^[0-2][0-9]:[0-5][0-9]$" }
        green_window_end:   { type: string, pattern: "^[0-2][0-9]:[0-5][0-9]$" }
        price_cents: { type: integer, minimum: 0 }
        revenue_split:
          type: object
          properties:
            pool_pct: { type: integer, minimum: 0, maximum: 100 }
            activator_pct: { type: integer, minimum: 0, maximum: 100 }
          required: [pool_pct, activator_pct]
        capacity: { type: integer, nullable: true }
        visibility: { type: string, enum: [public, followers, private], default: public }
      required: [title, city, lat, lng, starts_at, ends_at]

    Event:
      type: object
      properties:
        id: { type: integer }
        title: { type: string }
        description: { type: string }
        category: { type: string }
        city: { type: string }
        lat: { type: number }
        lng: { type: number }
        starts_at: { type: string, format: date-time }
        ends_at: { type: string, format: date-time }
        green_window:
          type: object
          nullable: true
          properties:
            start: { type: string }
            end:   { type: string }
        price_cents: { type: integer }
        capacity: { type: integer, nullable: true }
        visibility: { type: string }
        status: { type: string }
      required: [id, title, city, lat, lng, starts_at, ends_at, price_cents, visibility, status]

    EventNearby:
      type: object
      properties:
        id: { type: integer }
        title: { type: string }
        distance_m: { type: number }
        starts_at: { type: string, format: date-time }
        ends_at: { type: string, format: date-time }
        price_cents: { type: integer }
        green_window:
          type: object
          nullable: true
          properties:
            start: { type: string }
            end:   { type: string }
        capacity_left: { type: integer, nullable: true }
      required: [id, title, distance_m, starts_at, ends_at, price_cents]

    EventJoinRes:
      type: object
      properties:
        attendance_id: { oneOf: [ { type: string }, { type: integer } ] }
        state: { type: string, enum: [invited, joined, checked_in, verified, refunded] }
      required: [attendance_id, state]

    VerificationStartReq:
      type: object
      properties:
        mode: { type: string, enum: [geo, qr, photo], default: geo }
        charger_id: { oneOf: [ { type: string }, { type: integer } ], nullable: true }
      required: [mode]

    VerificationStartRes:
      type: object
      properties:
        verification_id: { type: string }
        status: { type: string, enum: [pending] }
      required: [verification_id, status]

    VerificationCompleteReq:
      type: object
      properties:
        lat: { type: number }
        lng: { type: number }
        photo_url: { type: string, nullable: true }
        qr_code: { type: string, nullable: true }
      required: [lat, lng]

    VerificationCompleteRes:
      type: object
      properties:
        verification_id: { type: string }
        status: { type: string, enum: [passed, failed] }
        reward_cents: { type: integer, nullable: true }
        pool_contribution_cents: { type: integer, nullable: true }
        message: { type: string, nullable: true }
      required: [verification_id, status]

    PoolSummaryRes:
      type: object
      properties:
        balance_cents: { type: integer }
        inflows:
          type: object
          additionalProperties: { type: integer }
        outflows:
          type: object
          additionalProperties: { type: integer }
        impact:
          type: object
          properties:
            verified_sessions: { type: integer }
            avg_reward_cents: { type: integer }
      required: [balance_cents, inflows, outflows, impact]
EOF

ok "OpenAPI spec saved to openapi-actions.yaml"

# Copy to the main directory
cp openapi-actions.yaml nerava-backend-v9/app/openapi-actions.yaml
ok "OpenAPI spec copied to API directory"

# Update CORS to allow ChatGPT and tunnel
step "Updating CORS configuration"
export ALLOWED_ORIGINS="https://chat.openai.com,https://www.chatgpt.com,$TUNNEL_URL"
ok "CORS updated (allow origins: chat.openai.com, chatgpt.com, and tunnel)"

# Instructions
step "Next Steps:"
echo ""
echo "1. Copy the tunnel URL and OpenAPI spec URL:"
echo "   Tunnel: $TUNNEL_URL"
echo "   Spec: $TUNNEL_URL/openapi-actions.yaml"
echo ""
echo "2. In ChatGPT, go to Create GPT → Configure → Actions → Import from URL"
echo "   Paste: $TUNNEL_URL/openapi-actions.yaml"
echo ""
echo "3. Set Authentication:"
echo "   Type: API Key"
echo "   Header: X-Api-Key"
echo "   Value: (leave empty for demo, or set ACTIONS_API_KEY in env)"
echo ""
echo "4. Test by asking ChatGPT:"
echo "   'Find coffee merchants near 30.2672, -97.7431'"
echo ""
echo "⚠️  Note: These URLs will expire when you stop the tunnel."
echo ""
echo "To stop everything:"
echo "  kill $API_PID $TUNNEL_PID"


# Multi-stage build for Next.js landing page
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
# NEXT_PUBLIC_BASE_PATH will be set at build time via build arg
ARG NEXT_PUBLIC_BASE_PATH
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
ARG NEXT_PUBLIC_ANALYTICS_ENABLED=true
ARG NEXT_PUBLIC_DRIVER_APP_URL
ARG NEXT_PUBLIC_MERCHANT_APP_URL
ARG NEXT_PUBLIC_CHARGER_PORTAL_URL
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH:-''}
ENV NEXT_PUBLIC_POSTHOG_KEY=${NEXT_PUBLIC_POSTHOG_KEY}
ENV NEXT_PUBLIC_POSTHOG_HOST=${NEXT_PUBLIC_POSTHOG_HOST}
ENV NEXT_PUBLIC_ANALYTICS_ENABLED=${NEXT_PUBLIC_ANALYTICS_ENABLED}
ENV NEXT_PUBLIC_DRIVER_APP_URL=${NEXT_PUBLIC_DRIVER_APP_URL}
ENV NEXT_PUBLIC_MERCHANT_APP_URL=${NEXT_PUBLIC_MERCHANT_APP_URL}
ENV NEXT_PUBLIC_CHARGER_PORTAL_URL=${NEXT_PUBLIC_CHARGER_PORTAL_URL}
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set correct permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start Next.js production server
CMD ["node", "server.js"]


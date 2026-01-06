# Multi-stage build for Vite driver app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build arguments for Vite
ARG VITE_PUBLIC_BASE=/app/
ARG VITE_API_BASE_URL=https://api.nerava.network
ARG VITE_ENV=prod
ARG VITE_POSTHOG_KEY
ARG VITE_POSTHOG_HOST=https://app.posthog.com
ARG VITE_ANALYTICS_ENABLED=true
ENV VITE_PUBLIC_BASE=${VITE_PUBLIC_BASE}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_ENV=${VITE_ENV}
ENV VITE_MOCK_MODE=false
ENV VITE_POSTHOG_KEY=${VITE_POSTHOG_KEY}
ENV VITE_POSTHOG_HOST=${VITE_POSTHOG_HOST}
ENV VITE_ANALYTICS_ENABLED=${VITE_ANALYTICS_ENABLED}

# Build-time validation: fail if API URL is invalid in production
RUN if [ "$VITE_ENV" = "prod" ] || [ "$VITE_ENV" = "production" ]; then \
      if [ "$VITE_API_BASE_URL" = "/api" ] || echo "$VITE_API_BASE_URL" | grep -q "^http://localhost"; then \
        echo "ERROR: VITE_API_BASE_URL cannot be '/api' or 'http://localhost:*' in production builds" && \
        echo "Current value: $VITE_API_BASE_URL" && \
        echo "Set VITE_API_BASE_URL to your production API URL (e.g., https://api.nerava.network)" && \
        exit 1; \
      fi; \
    fi

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3001/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]


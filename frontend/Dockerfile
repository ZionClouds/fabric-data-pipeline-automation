# ============================================================================
# STAGE 1: Build React App
# ============================================================================
FROM node:18-alpine AS build

WORKDIR /app
RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi

COPY . .

# Build-time args (optional defaults)
ARG REACT_APP_API_URL
ARG REACT_APP_WORKSPACE_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WORKSPACE_API_URL=$REACT_APP_WORKSPACE_API_URL

RUN npm run build

# ============================================================================
# STAGE 2: Serve with Nginx + Runtime Env Injection
# ============================================================================
FROM nginx:alpine

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets
COPY --from=build /app/build /usr/share/nginx/html

# --------------------------------------------------------------------------
# Runtime env injection
# --------------------------------------------------------------------------
# Create template file that will be rewritten at container startup
RUN echo 'window._env_ = { REACT_APP_API_URL: "PLACEHOLDER_API_URL" };' \
      > /usr/share/nginx/html/env-config.js

# Add startup script for runtime environment injection
RUN printf '#!/bin/sh\n\
set -e\n\
echo "[INFO] Starting Nginx on port 8080..."\n\
\n\
# Inject runtime environment variables into env-config.js\n\
if [ -n "$REACT_APP_API_URL" ]; then\n\
  echo "[INFO] Injecting REACT_APP_API_URL: $REACT_APP_API_URL"\n\
  sed -i "s|PLACEHOLDER_API_URL|$REACT_APP_API_URL|g" /usr/share/nginx/html/env-config.js\n\
else\n\
  echo "[WARN] REACT_APP_API_URL not set at runtime; using build-time value or placeholder."\n\
fi\n\
\n\
exec nginx -g "daemon off;"\n' > /docker-entrypoint.sh \
    && chmod +x /docker-entrypoint.sh

# Environment
ENV PORT=8080
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Start Nginx
CMD ["/docker-entrypoint.sh"]

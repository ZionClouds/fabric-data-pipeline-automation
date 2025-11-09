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

# Add startup script
RUN echo '#!/bin/sh\n\
set -e\n\
echo "[INFO] Starting Nginx on port 8080..."\n\
sed -i "s/listen 80;/listen 8080;/g" /etc/nginx/conf.d/default.conf\n\
if [ -z "$REACT_APP_API_URL" ]; then\n\
  echo "[WARN] REACT_APP_API_URL not set; using placeholder.";\n\
else\n\
  sed -i "s|PLACEHOLDER_API_URL|$REACT_APP_API_URL|g" /usr/share/nginx/html/env-config.js;\n\
fi\n\
exec nginx -g \"daemon off;\"' > /docker-entrypoint.sh \
    && chmod +x /docker-entrypoint.sh

# Environment
ENV PORT=8080
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Start Nginx
CMD ["/docker-entrypoint.sh"]

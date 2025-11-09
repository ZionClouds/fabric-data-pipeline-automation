# ============================================================================
# Build stage - React Application
# ============================================================================
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# --- native toolchain for Alpine (needed by some deps) ---
RUN apk add --no-cache python3 make g++

# Copy and install dependencies (robust to missing lockfile)
COPY package*.json ./
RUN set -eux; \
    if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi

# Bring in the rest of the app
COPY . .

# Build-time args for React environment variables
ARG REACT_APP_API_URL
ARG REACT_APP_WORKSPACE_API_URL

# Expose public vars as ENV for build
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WORKSPACE_API_URL=$REACT_APP_WORKSPACE_API_URL

# Build the React app
RUN npm run build

# ============================================================================
# Production stage - Nginx Server
# ============================================================================
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Create a startup script to handle port configuration
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Starting nginx on port 8080..."\n\
# Replace default port 80 with 8080 in nginx config\n\
sed -i "s/listen 80;/listen 8080;/g" /etc/nginx/conf.d/default.conf\n\
# Start nginx\n\
exec nginx -g "daemon off;"' > /docker-entrypoint.sh \
    && chmod +x /docker-entrypoint.sh

# Runtime
ENV PORT=8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Start nginx with custom entrypoint
CMD ["/docker-entrypoint.sh"]

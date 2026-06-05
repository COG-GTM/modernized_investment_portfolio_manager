# syntax=docker/dockerfile:1

# ---- Stage 1: build the static frontend ----
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json package-lock.json ./
RUN npm ci

# Build the Vite app. VITE_API_BASE_URL defaults to "/api" so the browser
# calls the same origin and nginx proxies through to the backend service.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY . .
RUN npm run build


# ---- Stage 2: serve with nginx ----
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD wget -qO- http://localhost:80/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]

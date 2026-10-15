# ---- Stage 1: build the React app ----
FROM node:22-alpine AS build
WORKDIR /app

# Install dependencies first: this layer is cached until package files change.
# Uses the exact versions from package-lock.json when it exists (npm ci),
# otherwise falls back to npm install.
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
RUN npm run build

# ---- Stage 2: serve static files with nginx ----
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

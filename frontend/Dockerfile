# QuickRx frontend — Vite build served by nginx, which also proxies /api/v1
# to the backend container so the browser talks to a single origin.
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Served from the domain root in Docker (not /quickrx/ like GitHub Pages),
# and the API is same-origin via the nginx proxy.
ENV VITE_API_URL=/api/v1
RUN npm run build -- --base=/

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

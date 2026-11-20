# 构建上下文为仓库根目录（见 deploy/docker-compose.yml）
FROM node:20-alpine AS builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY frontend/index.html frontend/tsconfig*.json frontend/vite.config.ts frontend/eslint.config.ts ./
COPY frontend/src ./src
COPY frontend/tests ./tests
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

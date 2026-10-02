FROM node:22-alpine
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
ENV VITE_MATCHING_API_URL=http://127.0.0.1:8000
EXPOSE 3000
CMD ["pnpm", "dev", "--", "--hostname", "0.0.0.0"]

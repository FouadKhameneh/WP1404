FROM node:20-alpine

WORKDIR /app/frontend

RUN npm install -g npm@latest

EXPOSE 3000

CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port 3000"]

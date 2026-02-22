FROM node:20-alpine

WORKDIR /app/frontend

RUN npm install -g npm@latest
COPY frontend /app/frontend
RUN if [ -f package.json ]; then npm install; fi

EXPOSE 3000

CMD ["sh", "-c", "if [ -f package.json ]; then npm run dev -- --host 0.0.0.0 --port 3000; else echo frontend-not-initialized; sleep infinity; fi"]

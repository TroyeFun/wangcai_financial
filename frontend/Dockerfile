ARG BASE_IMAGE=node:18-alpine
FROM ${BASE_IMAGE}

WORKDIR /app

ARG NPM_REGISTRY=

COPY package*.json ./

# Optional npm registry (e.g. npmmirror in China)
RUN if [ -n "$NPM_REGISTRY" ]; then npm config set registry "$NPM_REGISTRY"; fi \
    && npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

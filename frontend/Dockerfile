FROM node:22-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV REACT_APP_API_URL=http://localhost:8001
CMD ["npm", "start"]

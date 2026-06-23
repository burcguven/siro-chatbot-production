FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_CHATBOT_BACKEND_API
ENV VITE_CHATBOT_BACKEND_API=$VITE_CHATBOT_BACKEND_API

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

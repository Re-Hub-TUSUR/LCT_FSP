FROM nginx:1.29-alpine

RUN apk add --no-cache openssl

ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1 \
    FRONTEND_UPSTREAM=http://frontend:81

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO /dev/null http://127.0.0.1/healthz || exit 1

# ── build ──
FROM python:3.12-slim AS build
WORKDIR /docs
RUN pip install --no-cache-dir "zensical==0.0.69"
COPY zensical.toml ./
COPY docs ./docs
RUN zensical build --clean

# ── serve ──
FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /docs/site /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO /dev/null http://127.0.0.1/ || exit 1

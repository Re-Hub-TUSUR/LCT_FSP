#!/bin/sh
# Builds the browser password file, then starts nginx. An empty list or secret keeps the port closed.
set -eu

close_door() {
  rm -f /etc/nginx/templates/default.conf.template
  cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
    listen 80;
    location = /healthz {
        default_type text/plain;
        return 200 "ok\n";
    }
    location / {
        default_type text/plain;
        return 503 "Админка не настроена\n";
    }
}
EOF
}

if [ -z "${ADMIN_GATE_USERS:-}" ] || [ -z "${ADMIN_GATE_SECRET:-}" ]; then
  echo "admin-gate: set ADMIN_GATE_USERS and ADMIN_GATE_SECRET; the door stays closed" >&2
  close_door
else
  printf '%s' "$ADMIN_GATE_SECRET" | grep -Eq '^[A-Za-z0-9_-]{16,}$' || {
    echo "admin-gate: ADMIN_GATE_SECRET must be 16+ characters from A-Za-z0-9_-" >&2
    exit 1
  }
  umask 077
  set -f
  : > /etc/nginx/admin.htpasswd
  old_ifs=$IFS
  IFS=','
  # shellcheck disable=SC2086
  for item in $ADMIN_GATE_USERS; do
    user=${item%%:*}
    pass=${item#*:}
    if [ "$user" = "$item" ] || [ -z "$user" ] || [ -z "$pass" ]; then
      echo "admin-gate: each entry in ADMIN_GATE_USERS is name:password" >&2
      exit 1
    fi
    printf '%s' "$user" | grep -Eq '^[A-Za-z0-9._-]{1,64}$' || {
      echo "admin-gate: user name must be A-Za-z0-9._-" >&2
      exit 1
    }
    # SHA-512 crypt instead of the MD5-based apr1: nginx hands it to musl crypt(), which knows it.
    hash=$(printf '%s' "$pass" | openssl passwd -6 -stdin)
    printf '%s:%s\n' "$user" "$hash" >> /etc/nginx/admin.htpasswd
  done
  IFS=$old_ifs
  chmod 644 /etc/nginx/admin.htpasswd
fi

exec /docker-entrypoint.sh nginx -g 'daemon off;'

#!/usr/bin/env bash
# Run the real application (PostgreSQL, Keycloak, API, worker, web) on this machine.
# Unlike the GitHub Pages demo, every screen reads and writes the local database.
#
#   scripts/local.sh up       build and start everything, wait until healthy
#   scripts/local.sh down     stop; data is kept in Docker volumes
#   scripts/local.sh status   show containers
#   scripts/local.sh logs     follow logs (optionally: logs api)
#   scripts/local.sh token    print an access token for librarian.dev (or: token admin.dev)
#   scripts/local.sh reset    stop and DELETE the local database and Keycloak data
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$root"
env_file="$root/.env"
placeholder="replace-with-a-local-password"
compose=(docker compose -f compose.yaml -f compose.local.yaml)

random_secret() {
  # 32 hex characters; never written anywhere but .env.
  od -An -N16 -tx1 /dev/urandom | tr -d ' \n'
}

value_of() {
  grep -E "^$1=" "$env_file" | tail -n 1 | cut -d= -f2- | tr -d "'\""
}

prepare_env() {
  if [ ! -f "$env_file" ]; then
    cp .env.example "$env_file"
    chmod 600 "$env_file"
    echo "Đã tạo .env từ .env.example"
  fi
  # Replace the example password only while no database was initialised with it.
  if [ "$(value_of POSTGRES_PASSWORD)" = "$placeholder" ] &&
    ! docker volume inspect lib-management_pgdata >/dev/null 2>&1; then
    secret="$(random_secret)"
    sed -i.bak "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD='$secret'/" "$env_file"
    rm -f "$env_file.bak"
    echo "Đã sinh POSTGRES_PASSWORD ngẫu nhiên trong .env"
  fi
  for name in KEYCLOAK_ADMIN_PASSWORD KEYCLOAK_DEV_USER_PASSWORD; do
    if ! grep -qE "^$name=" "$env_file"; then
      [ -z "$(tail -c 1 "$env_file")" ] || echo >>"$env_file"
      echo "$name=$(random_secret)" >>"$env_file"
      echo "Đã sinh $name trong .env"
    fi
  done
}

port_free() {
  ! (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
}

check_ports() {
  local keycloak_port="${KEYCLOAK_PORT:-$(value_of KEYCLOAK_PORT)}"
  local busy=()
  for entry in "web:5173" "api:${API_PORT:-$(value_of API_PORT)}" \
    "keycloak:${keycloak_port:-8080}" "postgres:${POSTGRES_PORT:-$(value_of POSTGRES_PORT)}"; do
    local port="${entry#*:}"
    [ -n "$port" ] || continue
    # A port held by this stack itself is fine (re-running up).
    if ! port_free "$port" &&
      ! docker ps --filter label=com.docker.compose.project=lib-management --format '{{.Ports}}' |
      grep -q ":$port->"; then
      busy+=("${entry%%:*} ($port)")
    fi
  done
  if [ ${#busy[@]} -gt 0 ]; then
    echo "Cổng đang bị chiếm: ${busy[*]}" >&2
    echo "Tắt chương trình đang dùng cổng, hoặc đổi API_PORT / KEYCLOAK_PORT / POSTGRES_PORT trong .env." >&2
    echo "Cổng web 5173 là cố định (Keycloak chỉ cho redirect về http://localhost:5173)." >&2
    exit 1
  fi
}

case "${1:-up}" in
  up)
    command -v docker >/dev/null || { echo "Cần cài Docker Desktop/Engine." >&2; exit 1; }
    prepare_env
    check_ports
    "${compose[@]}" up --build -d --wait
    keycloak_port="${KEYCLOAK_PORT:-$(value_of KEYCLOAK_PORT)}"
    cat <<EOF

Lib-management đang chạy với dữ liệu thật trên máy này:
  Ứng dụng     http://localhost:5173
  API/Swagger  http://localhost:${API_PORT:-$(value_of API_PORT)}/docs
  Keycloak     http://localhost:${keycloak_port:-8080}  (admin / KEYCLOAK_ADMIN_PASSWORD trong .env)

Tài khoản đăng nhập: librarian.dev, manager.dev, admin.dev, ops.dev, reader.dev
Mật khẩu chung: giá trị KEYCLOAK_DEV_USER_PASSWORD trong .env
Dừng: scripts/local.sh down   (dữ liệu được giữ lại)
EOF
    ;;
  down)
    "${compose[@]}" down
    ;;
  status)
    "${compose[@]}" ps
    ;;
  logs)
    shift
    "${compose[@]}" logs -f "$@"
    ;;
  token)
    # Passed by name so the password never appears on a command line.
    KEYCLOAK_DEV_USER_PASSWORD="$(value_of KEYCLOAK_DEV_USER_PASSWORD)"
    export KEYCLOAK_DEV_USER_PASSWORD
    "${compose[@]}" exec -T -e KEYCLOAK_DEV_USER_PASSWORD api python - "${2:-librarian.dev}" <<'EOF'
import json, os, sys, urllib.parse, urllib.request
form = urllib.parse.urlencode({
    "grant_type": "password", "client_id": "lib-management-dev-cli",
    "username": sys.argv[1], "password": os.environ["KEYCLOAK_DEV_USER_PASSWORD"],
}).encode()
url = "http://keycloak:8080/realms/lib-management/protocol/openid-connect/token"
print(json.load(urllib.request.urlopen(url, form, timeout=10))["access_token"])
EOF
    ;;
  reset)
    read -r -p "Xóa toàn bộ dữ liệu local (database + Keycloak)? Gõ 'xoa' để xác nhận: " answer
    [ "$answer" = "xoa" ] || { echo "Đã hủy."; exit 1; }
    "${compose[@]}" down --volumes
    ;;
  *)
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac

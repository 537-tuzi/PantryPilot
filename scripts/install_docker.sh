#!/usr/bin/env bash
# 安装 Docker Engine + Compose v2，并配置镜像加速器。
# 用法：sudo bash scripts/install_docker.sh
# 说明：需要 root 权限；脚本会同时把当前用户加入 docker 组。
set -euo pipefail

MIRROR="${DOCKER_MIRROR:-https://docker.1ms.run}"
INVOKED_USER="${SUDO_USER:-$(id -un)}"

info() { printf '\033[0;36m==>\033[0m %s\n' "$1"; }
ok()   { printf '\033[0;32m[OK]\033[0m %s\n' "$1"; }
die()  { printf '\033[0;31m[x]\033[0m %s\n' "$1" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || { exec sudo -E bash "$0" "$@"; }

info "系统信息"
. /etc/os-release
ok "${PRETTY_NAME} / $(uname -m)"

info "更新 apt 并安装基础依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg uidmap >/dev/null
ok "基础依赖就绪"

info "配置 Docker 官方 apt 源"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
ok "apt 源已写入 /etc/apt/sources.list.d/docker.list"

info "安装 Docker Engine 与 Compose 插件"
apt-get update -qq
apt-get install -y -qq \
  docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin >/dev/null
ok "安装完成：$(docker --version)"

info "写入镜像加速器配置"
install -m 0644 /dev/null /etc/docker/daemon.json
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": ["${MIRROR}"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
ok "/etc/docker/daemon.json 已写入 registry-mirrors: ${MIRROR}"

info "启动 Docker 服务"
systemctl daemon-reload
systemctl enable --now docker
systemctl restart docker
sleep 2
systemctl is-active --quiet docker && ok "docker 服务运行中" || die "docker 服务启动失败：journalctl -u docker -n 50"

info "把用户加入 docker 组"
if [ "$INVOKED_USER" != "root" ]; then
  usermod -aG docker "$INVOKED_USER"
  ok "$INVOKED_USER 已加入 docker 组（需重新登录或执行 newgrp docker 生效）"
fi

info "验证镜像加速器"
docker info 2>/dev/null | sed -n '/Registry Mirrors/,+2p' | sed 's/^/    /'

info "拉取镜像测试（验证加速器是否真的可用）"
if docker pull hello-world:latest >/dev/null 2>&1; then
  ok "hello-world 拉取成功，镜像加速器可用"
  docker rmi hello-world:latest >/dev/null 2>&1 || true
else
  printf '\033[0;33m[!]\033[0m 拉取失败，请检查网络或更换加速器地址\n'
fi

cat <<EOF

安装完成。
  验证：docker version && docker compose version
  启动项目：
    cd <项目根目录>
    cp .env.example .env && vi .env
    bash scripts/bootstrap.sh
    docker compose -f deploy/docker-compose.yml up -d --build
  注意：刚被加入 docker 组的用户需要重新登录（或执行 newgrp docker）才能免 sudo 使用 docker。
EOF

#!/usr/bin/env bash
# Prepares a fresh Ubuntu VM: Docker + docker group + nginx reverse proxy.
# Called by the deploy job on EVERY run, so it is idempotent:
# it only installs what is missing and just re-applies the nginx config otherwise.
#
# Expects ~/app/nginx-vm.conf to exist (the pipeline copies it there first).

set -euo pipefail

USER_NAME="$(id -un)"

echo "==> Waiting for the VM's first-boot tasks (cloud-init) to finish"
sudo cloud-init status --wait >/dev/null 2>&1 || true

echo "==> Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
else
  echo "already installed: $(docker --version)"
fi
sudo systemctl enable --now docker

echo "==> docker group + user"
getent group docker >/dev/null || sudo groupadd docker
if ! id -nG "$USER_NAME" | grep -qw docker; then
  sudo usermod -aG docker "$USER_NAME"
  echo "added $USER_NAME to the docker group (active from the next SSH session)"
fi

echo "==> nginx"
if ! command -v nginx >/dev/null 2>&1; then
  sudo apt-get -o DPkg::Lock::Timeout=180 update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=180 install -y nginx
else
  echo "already installed: $(nginx -v 2>&1)"
fi

sudo install -m 644 "$HOME/app/nginx-vm.conf" /etc/nginx/sites-available/app
sudo ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx || sudo systemctl restart nginx

echo "==> VM ready"

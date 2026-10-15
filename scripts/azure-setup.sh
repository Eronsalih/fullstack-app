#!/usr/bin/env bash
# One-time Azure setup: resource group + Ubuntu VM with Docker + open port 80.
#
# Requirements: Azure CLI installed and logged in (az login).
# Usage:        bash scripts/azure-setup.sh
# Override any value:   VM_SIZE=Standard_B1s LOCATION=northeurope bash scripts/azure-setup.sh

set -euo pipefail

RG="${RG:-fullstack-rg}"
LOCATION="${LOCATION:-westeurope}"
VM_NAME="${VM_NAME:-fullstack-vm}"
VM_SIZE="${VM_SIZE:-Standard_B2s}"
ADMIN_USER="${ADMIN_USER:-azureuser}"   # keep in sync with scripts/cloud-init.yml
KEY_PATH="${KEY_PATH:-$HOME/.ssh/azure_deploy}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Creating resource group '$RG' in '$LOCATION'"
az group create --name "$RG" --location "$LOCATION" --output none

if [ ! -f "$KEY_PATH" ]; then
  echo "==> Generating a dedicated SSH key for deployments: $KEY_PATH"
  ssh-keygen -t ed25519 -f "$KEY_PATH" -N "" -C "github-actions-deploy"
fi

echo "==> Creating VM '$VM_NAME' ($VM_SIZE) - this takes 1-2 minutes"
az vm create \
  --resource-group "$RG" \
  --name "$VM_NAME" \
  --image Ubuntu2204 \
  --size "$VM_SIZE" \
  --admin-username "$ADMIN_USER" \
  --ssh-key-values "${KEY_PATH}.pub" \
  --public-ip-sku Standard \
  --custom-data "$SCRIPT_DIR/cloud-init.yml" \
  --output none

echo "==> Opening port 80 (HTTP). Port 22 (SSH) is opened by az vm create."
az vm open-port --resource-group "$RG" --name "$VM_NAME" --port 80 --priority 1010 --output none

IP="$(az vm show --resource-group "$RG" --name "$VM_NAME" --show-details --query publicIps --output tsv)"

echo "==> Waiting for Docker installation (cloud-init) to finish..."
for i in $(seq 1 20); do
  if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
       "$ADMIN_USER@$IP" "cloud-init status --wait" >/dev/null 2>&1; then
    break
  fi
  sleep 10
done

cat <<EOF

================ DONE ================
VM public IP : $IP

Add these 5 secrets in GitHub:
  Repo -> Settings -> Secrets and variables -> Actions -> New repository secret

  AZURE_VM_HOST     $IP
  AZURE_VM_USER     $ADMIN_USER
  AZURE_VM_SSH_KEY  (the full content of: $KEY_PATH)   <- cat $KEY_PATH
  MONGO_USER        admin
  MONGO_PASSWORD    (choose a long password: letters and numbers only)

Then push to the main branch. After the pipeline is green open: http://$IP
Test SSH manually:  ssh -i $KEY_PATH $ADMIN_USER@$IP
======================================
EOF

#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  Provenance-aware deploy wrapper
# ============================================================

NETWORK=${1:-"base-mainnet"}
CONTRACT=${2:-"SuperpositionKernel"}
DEPLOY_SCRIPT=${DEPLOY_SCRIPT:-"forge script"}
OUTPUT_DIR="deployments/$NETWORK"
META_FILE="$OUTPUT_DIR/${CONTRACT}.meta.json"

mkdir -p "$OUTPUT_DIR"

# --- Step 1: Run provenance commit ---------------------------
./scripts/provenance.sh

# Extract values from the provenance log
HASH=$(awk '{print $1}' docs/disclosure.hash)
TAG=$(git describe --tags --abbrev=0)
TIMESTAMP=$(git log -1 --format=%cI)

echo "🔗 Disclosure $TAG ($HASH) @ $TIMESTAMP"

# --- Step 2: Deploy contract (Foundry example) ----------------
$DEPLOY_SCRIPT script/Deploy${CONTRACT}.s.sol \
  --broadcast --rpc-url $RPC_URL --verify

# Capture deployed address
ADDR=$(grep -E "Deployed to:" broadcast/Deploy${CONTRACT}.s.sol/1/run-latest.log | awk '{print $3}')

# --- Step 3: Record metadata ----------------------------------
cat > "$META_FILE" <<EOF
{
  "contract": "$CONTRACT",
  "network": "$NETWORK",
  "address": "$ADDR",
  "disclosure_tag": "$TAG",
  "disclosure_hash": "$HASH",
  "timestamp": "$TIMESTAMP"
}
EOF

echo "✅ Metadata written to $META_FILE"

# --- Step 4: Optional on-chain log -----------------------------
# Emits an event from a lightweight ProvenanceRegistry contract.
# You can deploy a registry once and reuse it.
if [ -n "${REGISTRY_ADDR:-}" ]; then
  echo "⛓️  Registering provenance hash on-chain via registry"
  cast send $REGISTRY_ADDR \
    "registerDisclosure(string,string,string)" \
    "$TAG" "$HASH" "$ADDR" \
    --rpc-url $RPC_URL --private-key $PRIVATE_KEY
fi

echo "Deployment complete for $CONTRACT on $NETWORK"

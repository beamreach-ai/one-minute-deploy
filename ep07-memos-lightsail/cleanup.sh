#!/bin/bash
# Tear down everything the episode created: delete the container service (its
# containers, https endpoint and stored data go with it) and wait until
# Lightsail no longer lists it. The name stays reserved for a few more minutes.
# Usage: ./cleanup.sh [service-name]     (uses your AWS CLI region, or AWS_REGION)
set -e
SERVICE=${1:-memos}
set -x
aws lightsail delete-container-service --service-name "$SERVICE"
set +x
for _ in $(seq 1 120); do
  aws lightsail get-container-services --service-name "$SERVICE" >/dev/null 2>&1 || { echo "gone: $SERVICE"; exit 0; }
  sleep 5
done
echo "still deleting after 10 minutes: check 'aws lightsail get-container-services'" >&2; exit 1

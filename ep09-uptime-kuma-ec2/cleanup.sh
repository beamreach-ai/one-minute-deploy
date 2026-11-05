#!/bin/bash
# Tear down everything the episode created: delete the stack (server, firewall,
# network) and wait until it is gone.
# Usage: ./cleanup.sh [stack-name]
set -e
STACK=${1:-kuma}
set -x
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"

#!/bin/bash
# Tear down everything the episode created: delete the stack (service, task
# definition, cluster, firewall, network) and wait until it is gone.
# Usage: ./cleanup.sh [stack-name]
set -e
STACK=${1:-speedtest}
set -x
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"

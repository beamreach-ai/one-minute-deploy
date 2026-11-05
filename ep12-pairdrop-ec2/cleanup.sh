#!/bin/bash
# Tear down everything the episode created: deleting the stack removes the
# instance and its VPC. Waits until it is gone.
# Usage: ./cleanup.sh [stack-name]
set -e
STACK=${1:-pairdrop}
set -x
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"

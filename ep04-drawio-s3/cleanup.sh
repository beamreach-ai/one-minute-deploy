#!/bin/bash
# Tear down everything the episode created: empty the bucket, delete the stack.
# Usage: ./cleanup.sh <your-bucket-name> [stack-name]
set -e
BUCKET=${1:?usage: ./cleanup.sh <bucket-name> [stack-name]}; STACK=${2:-drawio}
set -x
aws s3 rm "s3://$BUCKET" --recursive --quiet
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"

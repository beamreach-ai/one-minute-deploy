#!/bin/bash
# Tear down everything the episode created: empty the bucket, delete the stack
# (bucket, CloudFront distribution, access control, bucket policy).
# CloudFront takes a few minutes to switch off, so the last command waits.
# Usage: ./cleanup.sh <your-bucket-name> [stack-name]
set -e
BUCKET=${1:?usage: ./cleanup.sh <bucket-name> [stack-name]}; STACK=${2:-excalidraw}
set -x
aws s3 rm "s3://$BUCKET" --recursive --quiet
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"

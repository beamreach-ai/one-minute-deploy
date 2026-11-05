#!/bin/bash
# Tear down everything the episode created: delete the stack (CloudFront
# distribution, service, load balancer, network) and wait until it is gone.
# Deleting the CloudFront distribution is the slow part: allow 5 to 10 minutes.
# Usage: ./cleanup.sh [stack-name]
set -e
STACK=${1:-actual}
set -x
aws cloudformation delete-stack --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --stack-name "$STACK"

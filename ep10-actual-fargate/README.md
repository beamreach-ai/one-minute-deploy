# ep.10 · Actual Budget on ECS Fargate, with CloudFormation

Run [Actual Budget](https://github.com/actualbudget/actual) (MIT), a personal
budgeting app, as a container on ECS Fargate. Actual's web app needs a secure
context, so a bare `http://` address is not enough: the container sits behind
an Application Load Balancer, with a CloudFront distribution in front for https
on its free `*.cloudfront.net` address. No domain and no certificate to buy.
One template, three commands. In the video it took 5 min 49 s from the first
command until the app answered.

## Deploy

```bash
# 1 · get the template and see what it will create
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep10-actual-fargate/actual.yaml
grep AWS:: actual.yaml

# 2 · pick the version: change CHANGE-ME to latest (or a release such as 26.11.0)
nano actual.yaml

# 3 · create everything (CloudFront is the slow part)
aws cloudformation deploy \
  --stack-name actual \
  --template-file actual.yaml
```

Get the address:

```bash
aws cloudformation describe-stacks --stack-name actual \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

It looks like `https://d1234abcd.cloudfront.net`. Then:

1. Set the server password (the first visitor gets to do this, so do it right
   away), and sign in with it.
2. *Start budgeting* for an empty budget, or *Try the demo* for one full of
   made-up numbers.

## What the template creates

[`actual.yaml`](actual.yaml) is the whole infrastructure. It brings its own
network, so it also works in an account or region without a default VPC:

- **`Network`, `Gateway`, `GatewayLink`, `Routes`, `InternetRoute`, `SubnetA`,
  `SubnetB` and their route links**: a VPC with two public subnets (a load
  balancer needs two zones) and a route to the internet. No NAT gateway.
- **`WebFirewall`, `AppFirewall`**: security groups. Port 80 is open to the
  load balancer; port 5006 on the container is open only to the load balancer.
- **`Balancer`, `Targets`, `Listener`**: an Application Load Balancer that
  forwards to the container.
- **`Cluster`, `Task`, `Service`**: an ECS cluster, the task definition (the
  public image `actualbudget/actual-server` with 0.25 vCPU and 0.5 GB) and a
  service that keeps one copy running on Fargate. The public IP on the task is
  only there so it can pull the image without a NAT gateway; its firewall
  accepts nothing except the load balancer.
- **`Https`**: a CloudFront distribution in front of the load balancer. Caching
  is off and all headers, cookies, query strings and methods are passed through
  (AWS's managed `CachingDisabled` and `AllViewer` policies), so it does nothing
  except add https.

There is no IAM role in the template: the image is public and the task sends no
logs anywhere, so it needs no permissions.

## What it costs

About **5 cents per hour** in us-west-1 while it runs: the load balancer (about
$0.025/h), Fargate at 0.25 vCPU and 0.5 GB (about $0.014/h), and public IPv4
addresses ($0.005/h each: one for the task, one per load balancer zone).
CloudFront costs next to nothing at this traffic. Delete it when you are done:
left running, that is about $35 a month.

## Things worth knowing

- **Why not plain http?** Open the load balancer's `http://` address and Actual
  stops at a *Fatal Error*: it needs `SharedArrayBuffer`, which browsers only
  allow in a secure context. CloudFront's default certificate is the cheapest
  way to get https without owning a domain.
- **Your data is not durable here.** The budget files live on the task's own
  disk, so they are lost whenever the task is replaced or the stack is deleted.
  This is a demo. For real use add an EFS volume mounted at `/data`.
- The load balancer's own `http://` address stays open to the world, so it can
  be reached without going through CloudFront. For real use, limit `WebFirewall`
  to CloudFront's managed prefix list.
- CloudFront to the load balancer is plain http inside AWS. Only the part
  between you and CloudFront is encrypted.
- The password screen is open until someone sets a password. Set yours right
  after the deploy.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep10-actual-fargate/cleanup.sh
bash cleanup.sh
```

It deletes the stack and waits until it is gone. CloudFront has to disable the
distribution first, so this takes several minutes.

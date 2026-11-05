# ep.09 · Uptime Kuma on an EC2 instance, with CloudFormation

Run [Uptime Kuma](https://github.com/louislam/uptime-kuma) (by Louis Lam, MIT),
a self-hosted uptime monitor, on one small server: an EC2 instance that
installs Docker on first boot and starts the official container image on
port 80. One template, three commands. In the video it took 2 min 22 s from
the first command until the app answered.

## Deploy

```bash
# 1 · get the template and see what it will create
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep09-uptime-kuma-ec2/kuma.yaml
grep Type: kuma.yaml

# 2 · pick the server size: change CHANGE-ME to t3.micro
nano kuma.yaml

# 3 · create the network and the server (about 80 s)
aws cloudformation deploy \
  --stack-name kuma \
  --template-file kuma.yaml
```

Get the address:

```bash
aws cloudformation describe-stacks --stack-name kuma \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

It looks like `http://<the server's public IP>`. The stack is finished as soon
as the server is *running*; the server then needs about another minute to
install Docker, pull the image and start the app. Until then the browser
cannot connect. Then:

1. Create the admin account (the first visitor gets to do this, so do it
   right away).
2. *Add* → type a URL → Enter. The first check runs at once and the monitor
   turns green.

## What the template creates

[`kuma.yaml`](kuma.yaml) is the whole infrastructure. It brings its own
network, so it also works in an account or region without a default VPC:

- **`Network`, `Gateway`, `GatewayLink`, `Routes`, `InternetRoute`, `Subnet`,
  `SubnetRoutes`**: a VPC with one public subnet and a route to the internet.
  No NAT gateway.
- **`Firewall`**: a security group that lets anyone in on port 80 and nothing
  else. There is no SSH access.
- **`Server`**: one EC2 instance on the latest Amazon Linux 2023 image (looked
  up from AWS's public SSM parameter, so the template works in any region).
  Its user data installs Docker and runs `louislam/uptime-kuma:2-slim`, with
  the data in a Docker volume on the instance's disk.

## What it costs

About **2 cents per hour** in us-west-1 while it runs: a `t3.micro` (about
$0.012/h), its public IPv4 address ($0.005/h) and 8 GB of disk. A new AWS
account may cover the instance with free tier.

## Things worth knowing

- `UPTIME_KUMA_DB_TYPE=sqlite` skips Uptime Kuma 2's "choose a database"
  screen, so the first run is only "create the admin account". The `2-slim`
  image leaves out the embedded MariaDB and Chromium, which makes the first
  boot faster.
- This is **http only**: the admin password travels unencrypted. Fine for a
  demo; for real use put https in front (a domain plus a reverse proxy such as
  Caddy on the instance, or a load balancer with a certificate).
- The public IP changes if you stop and start the instance. Add an Elastic IP
  if you need a fixed address.
- The data lives on the instance's disk. Deleting the stack deletes the
  monitors and their history.
- `t3.micro` (1 GB of memory) is enough for a few dozen monitors.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep09-uptime-kuma-ec2/cleanup.sh
bash cleanup.sh
```

It deletes the stack (server, firewall, network) and waits until it is gone.

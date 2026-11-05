# ep.11 · LibreSpeed on ECS Fargate, with CloudFormation

Run [LibreSpeed](https://github.com/librespeed/speedtest) (LGPL-3.0), a
self-hosted speed test, as a container on ECS Fargate: no server to manage,
one task with a public IP, no load balancer. One template, three commands. In
the video it took 1 min 48 s from the first command until the page answered.

## Deploy

```bash
# 1 · get the template and see what it will create
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep11-librespeed-fargate/speedtest.yaml
grep Type: speedtest.yaml

# 2 · name your speed test: change CHANGE-ME to the title you want on the page
nano speedtest.yaml

# 3 · create the network, the cluster and the service
aws cloudformation deploy \
  --stack-name speedtest \
  --template-file speedtest.yaml
```

The deploy returns when the container is running. A Fargate task gets its
public IP when it starts, so the address is not a stack output. Ask ECS for
the task, then for its network interface, then for the interface's address:

```bash
T=$(aws ecs list-tasks --cluster speedtest \
  --query 'taskArns[0]' --output text)
E=$(aws ecs describe-tasks --cluster speedtest --tasks $T --output text \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value")
aws ec2 describe-network-interfaces --network-interface-ids $E \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

Open `http://<that IP>` and press the start button.

## What the template creates

[`speedtest.yaml`](speedtest.yaml) is the whole infrastructure. It brings its
own network, so it also works in an account or region without a default VPC:

- **`Network`, `Gateway`, `GatewayLink`, `Routes`, `InternetRoute`, `Subnet`,
  `SubnetRoutes`**: a VPC with one public subnet and a route to the internet.
  No NAT gateway.
- **`Firewall`**: a security group that lets anyone in on port 80 and nothing
  else.
- **`Cluster`**: an ECS cluster named `speedtest`. A cluster is only a name to
  group things under; it costs nothing.
- **`Task`**: the task definition, which says what to run: the public image
  `ghcr.io/librespeed/speedtest` with 0.25 vCPU and 0.5 GB, port 80, and a few
  settings (standalone mode, the new design, your title).
- **`Service`**: keeps one copy of the task running on Fargate, in the public
  subnet with a public IP. If the container dies, the service starts a new one.

There is no IAM role in the template: the image is public, and the task sends
no logs anywhere, so it needs no permissions.

## What it costs

About **2 cents per hour** in us-west-1 while it runs: 0.25 vCPU and 0.5 GB on
Fargate (about $0.014/h) plus the public IPv4 address ($0.005/h).

Data is extra: a speed test downloads real data from your server, and AWS
charges about $0.09 per GB sent out to the internet (the first 100 GB per month
are free). A 12-second download test at 100 Mbit/s is about 150 MB.

## Things worth knowing

- The page shows the visitor's own IP address ("You are connected through").
  In the video it is blurred.
- The number you see is the speed between you and us-west-1 through a
  0.25 vCPU container, not your line's top speed. Deploy to a region near you
  (`--region`) for a fairer test, and give the task more CPU if the server is
  the limit.
- The public IP changes every time the task is replaced. For a fixed address
  put a load balancer in front (ep.10 does that).
- This is **http only**.
- Results are not stored: the template leaves LibreSpeed's telemetry off.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep11-librespeed-fargate/cleanup.sh
bash cleanup.sh
```

It deletes the stack (service, task definition, cluster, firewall, network)
and waits until it is gone.

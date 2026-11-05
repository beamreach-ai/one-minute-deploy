# ep.12 · PairDrop on an EC2 instance, with CloudFormation

[PairDrop](https://github.com/schlagmichdoch/PairDrop) (by schlagmichdoch,
GPL-3.0) sends files and messages between devices from a browser tab: open the
same address on two devices on one network and they see each other. It needs a
small server for the devices to find each other over WebSockets, so a bucket
is not enough: this episode starts one EC2 instance that installs Docker and
runs the PairDrop container. One template, three commands. In the video they
took 2 min 42 s in total, including the wait for the server to boot and pull the
image.

## Deploy

```bash
# 1 · get the template, and see what it will create
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep12-pairdrop-ec2/pairdrop.yaml
grep "Type: AWS::EC2" pairdrop.yaml

# 2 · switch on the relay fallback: change "Default: false" to "Default: true"
nano pairdrop.yaml

# 3 · create it all (about a minute, then a minute or two until the app answers)
aws cloudformation deploy \
  --stack-name pairdrop \
  --template-file pairdrop.yaml
```

Get the address and open it on two devices on the same network:

```bash
aws cloudformation describe-stacks --stack-name pairdrop \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

It looks like `http://<public-ip>`. The stack is "complete" as soon as the
instance exists; the server then still has to boot, install Docker and pull the
image, so give it a minute or two before the page loads.

Step 2 is optional. Instead of editing the file you can pass
`--parameter-overrides WsFallback=true` to the deploy.

## What the template creates

[`pairdrop.yaml`](pairdrop.yaml) does not rely on a default VPC, it brings its
own network:

- **`Vpc`**, **`Subnet`**: a tiny private network (`10.0.0.0/24`) with one
  public subnet.
- **`Gateway`**, **`GatewayToVpc`**, **`Routes`**, **`RouteOut`**,
  **`SubnetRoutes`**: an internet gateway and the route that sends the
  subnet's traffic through it.
- **`Firewall`**: a security group that lets the world in on port 80 and
  nothing else. There is no SSH.
- **`Server`**: one `t3.micro` instance on the newest Amazon Linux 2023 (the
  image id comes from AWS's public SSM parameter, so the template works in
  any region). Its user-data script runs once at first boot:

  ```bash
  dnf install -y docker
  systemctl enable --now docker
  docker run -d --restart always -p 80:3000 \
    -e WS_FALLBACK=<the WsFallback parameter> \
    ghcr.io/schlagmichdoch/pairdrop
  ```

No NAT gateway, no load balancer, no Elastic IP: the address changes if you
stop and start the instance.

## Things worth knowing

- **Who sees whom.** PairDrop puts devices that arrive from the same public IP
  address in one room, which is what "on this network" means. Anyone who has
  your address can open the page, but they only see devices behind their own
  IP. Devices on different networks (a phone on mobile data) can still be
  paired by hand with the buttons at the top.
- **The relay fallback** (`WS_FALLBACK`). Files normally travel straight from
  browser to browser over WebRTC, and the server only introduces the devices.
  With the fallback on, a device that cannot use WebRTC (most VPNs block it)
  sends through the server instead, and the page says so at the top. The
  server can read what is relayed, so only switch it on for a server you run
  yourself.
- This is **http only**. Sending still works, but browsers hold back some
  features without https (installing it as an app, the share menu, copying to
  the clipboard). PairDrop's own docs also expect a reverse proxy in front for
  a permanent setup; put one with a certificate there before you rely on it.
- A `t3.micro` costs about a cent an hour (free-tier eligible on new
  accounts). Delete the stack when you are done.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep12-pairdrop-ec2/cleanup.sh
bash cleanup.sh
```

It deletes the stack (instance, firewall, network) and waits until it is gone.

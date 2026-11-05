# ep.07 · Memos on a Lightsail container service, with the AWS CLI

[Memos](https://github.com/usememos/memos) (by usememos, MIT) is a self-hosted
notes app: write a thought, save it, find it later. It ships as a public
container image, so there is nothing to clone or build. An Amazon Lightsail
container service runs the image and gives it a public **https** address: two
CLI commands and one small file. In the video it took 3 min 21 s from the first
command to the app answering, nearly all of it Lightsail starting the service.

## Deploy

Lightsail is not offered in every AWS region (us-west-1 has none). Pick one
that has it, for example:

```bash
export AWS_REGION=us-west-2
```

```bash
# 1 · create a container service: the smallest size, one node
aws lightsail create-container-service \
  --service-name memos --power nano --scale 1

# 2 · get the container definition and pick the image:
#     change CHANGE-ME to neosmemo/memos:stable
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep07-memos-lightsail/memos.yaml
nano memos.yaml

# 3 · deploy the container
aws lightsail \
  create-container-service-deployment \
  --cli-input-yaml file://memos.yaml

# 4 · wait until it is running (several minutes)
until aws lightsail get-container-services \
  --service-name memos | grep -q RUNNING; \
  do sleep 5; done
```

Get the address and open it:

```bash
aws lightsail get-container-services --service-name memos \
  --query 'containerServices[0].url' --output text
```

It looks like `https://memos.<random-id>.<region>.cs.amazonlightsail.com/`.
The first visitor creates the admin account, so be that visitor.

## What gets created

- **A Lightsail container service** named `memos`: power `nano` (0.25 vCPU,
  512 MB), scale 1. It comes with a load balancer, a TLS certificate and the
  `https://memos.…cs.amazonlightsail.com` address. No VPC, no security groups,
  no IAM roles to set up.
- **One deployment** on it, described by [`memos.yaml`](memos.yaml): the image
  `neosmemo/memos:stable` pulled from Docker Hub, port 5230 opened inside the
  service, and the public endpoint pointed at that port.

## Things worth knowing

- **Storage is ephemeral.** Memos keeps its SQLite database inside the
  container, and a Lightsail container has no persistent disk. Every new
  deployment, restart or node replacement starts from an empty database: your
  account and your memos are gone. Fine for a look around; to keep notes, point
  Memos at an external MySQL or Postgres database (`MEMOS_DRIVER` and
  `MEMOS_DSN` under `environment:` in the file).
- **It is public.** Until someone creates the admin account, anyone who finds
  the address can, so open it as soon as it is running. After that the sign-up
  page is still offered to other visitors; look for the registration switch in
  the admin settings if you keep the service.
- **It costs money while it exists**: a `nano` service is about $7 a month,
  billed whether or not anyone uses it. Disabling the service does not stop
  the bill; deleting it does.
- **Do not open the address early.** Step 4 asks AWS for the state instead of
  trying the address, on purpose: the host name does not exist for the first
  minutes, and a computer that looks it up too soon can remember "no such
  host" for up to 15 minutes.
- If step 4 never returns, the deployment failed and the service fell back to
  `READY`. Stop it with Ctrl-C and read the reason with
  `aws lightsail get-container-log --service-name memos --container-name memos`.
- The first container service in a region takes longer, because Lightsail sets
  up networking and a certificate first. You can send the deployment right
  away, as here; it starts as soon as the service is ready.
- `stable` moves with each Memos release. For something you keep, pin a
  version tag such as `neosmemo/memos:26.11`.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep07-memos-lightsail/cleanup.sh
bash cleanup.sh
```

It deletes the container service (the container, the address and the data go
with it) and waits until Lightsail no longer lists it. The name `memos` stays
reserved for a few minutes after that: creating a service with the same name
straight away fails with "try again when service is done DELETING".

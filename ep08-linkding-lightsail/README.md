# ep.08 · linkding on a Lightsail container service, with the AWS CLI

[linkding](https://github.com/sissbruecker/linkding) (by Sascha Ißbrücker,
MIT) is a bookmark manager you host yourself: save a link, tag it, search it.
It ships as a public container image, so there is nothing to clone or build.
An Amazon Lightsail container service runs the image and gives it a public
**https** address: two CLI commands and one small file. In the video it took
4 min 54 s from the first command to the app answering, nearly all of it
Lightsail starting the service.

## Deploy

Lightsail is not offered in every AWS region (us-west-1 has none). Pick one
that has it, for example:

```bash
export AWS_REGION=us-west-2
```

```bash
# 1 · create a container service: the smallest size, one node
aws lightsail create-container-service \
  --service-name linkding --power nano --scale 1

# 2 · get the container definition and set your password:
#     change CHANGE-ME to a password of your own
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep08-linkding-lightsail/linkding.yaml
nano linkding.yaml

# 3 · deploy the container
aws lightsail \
  create-container-service-deployment \
  --cli-input-yaml file://linkding.yaml

# 4 · wait until it is running (several minutes)
until aws lightsail get-container-services \
  --service-name linkding | grep -q RUNNING; \
  do sleep 5; done
```

Get the address and open it:

```bash
aws lightsail get-container-services --service-name linkding \
  --query 'containerServices[0].url' --output text
```

It looks like `https://linkding.<random-id>.<region>.cs.amazonlightsail.com/`.
Log in as `demo` with the password you put in the file.

## What gets created

- **A Lightsail container service** named `linkding`: power `nano` (0.25 vCPU,
  512 MB), scale 1. It comes with a load balancer, a TLS certificate and the
  `https://linkding.…cs.amazonlightsail.com` address. No VPC, no security
  groups, no IAM roles to set up.
- **One deployment** on it, described by [`linkding.yaml`](linkding.yaml): the
  image `sissbruecker/linkding:latest` pulled from Docker Hub, port 9090 opened
  inside the service, the public endpoint pointed at that port with a health
  check on `/health`, and two settings, `LD_SUPERUSER_NAME` and
  `LD_SUPERUSER_PASSWORD`: linkding creates this user when it starts.

## Things worth knowing

- **Storage is ephemeral.** linkding keeps its SQLite database inside the
  container, and a Lightsail container has no persistent disk. Every new
  deployment, restart or node replacement starts from an empty database: your
  bookmarks are gone (the user is created again from the file). Fine for a
  look around; to keep bookmarks, point linkding at an external Postgres
  database (`LD_DB_ENGINE: postgres` and the other `LD_DB_*` settings).
- **The password is stored in plain text** in the file and in the deployment
  (`aws lightsail get-container-service-deployments` shows it). Use one you do
  not use anywhere else, and do not commit the edited file.
- **It is public.** Anyone who finds the address gets the login page, and the
  password is all that protects your bookmarks.
- **It costs money while it exists**: a `nano` service is about $7 a month,
  billed whether or not anyone uses it. Disabling the service does not stop
  the bill; deleting it does.
- **Do not open the address early.** Step 4 asks AWS for the state instead of
  trying the address, on purpose: the host name does not exist for the first
  minutes, and a computer that looks it up too soon can remember "no such
  host" for up to 15 minutes.
- If step 4 never returns, the deployment failed and the service fell back to
  `READY`. Stop it with Ctrl-C and read the reason with
  `aws lightsail get-container-log --service-name linkding --container-name linkding`.
- No `LD_CSRF_TRUSTED_ORIGINS` is needed here: logging in and saving work on
  the Lightsail https address as it is.
- The first container service in a region takes longer, because Lightsail sets
  up networking and a certificate first. You can send the deployment right
  away, as here; it starts as soon as the service is ready.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep08-linkding-lightsail/cleanup.sh
bash cleanup.sh
```

It deletes the container service (the container, the address and the data go
with it) and waits until Lightsail no longer lists it. The name `linkding` stays
reserved for a few minutes after that: creating a service with the same name
straight away fails with "try again when service is done DELETING".

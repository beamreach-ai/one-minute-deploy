# ep.02 · Excalidraw on S3 + CloudFront, with CloudFormation

Build [Excalidraw](https://github.com/excalidraw/excalidraw) (the hand-drawn
whiteboard, MIT) from source and serve it over **https** from a **private** S3
bucket behind CloudFront: one template, five commands. In the video the
commands took 11 minutes in total: six and a half for the build (on a busy
laptop) and four waiting for CloudFront.

## Deploy

You need Node 18 or newer and yarn 1 (`corepack enable` gives you yarn if you
only have Node). S3 bucket names are global, so pick your own. Replace
`my-excalidraw` below with the name you choose.

```bash
# 1 · get the code and the template
git clone --depth 1 \
  https://github.com/excalidraw/excalidraw
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep02-excalidraw-cloudfront/site.yaml

# 2 · install the dependencies and build the app (about 2 minutes)
(cd excalidraw && yarn && yarn build:app:docker)

# 3 · name your bucket: change CHANGE-ME to my-excalidraw
nano site.yaml

# 4 · create the bucket and the CloudFront distribution (about 4 minutes)
aws cloudformation deploy \
  --stack-name excalidraw \
  --template-file site.yaml

# 5 · upload the build
aws s3 sync excalidraw/excalidraw-app/build \
  s3://my-excalidraw
```

Get the address and open it:

```bash
aws cloudformation describe-stacks --stack-name excalidraw \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

It looks like `https://d1234abcd5678.cloudfront.net`.

## What the template creates

[`site.yaml`](site.yaml) is the whole infrastructure:

- **`Site`**: an S3 bucket. No website hosting, no public access: the bucket
  stays private.
- **`Access`**: a CloudFront *Origin Access Control*. It makes CloudFront sign
  its requests to S3, so S3 can tell them apart from everybody else's.
- **`CDN`**: a CloudFront distribution in front of the bucket. It serves
  `index.html` at `/`, redirects http to https, compresses the files and
  caches them at the edge.
- **`CdnRead`**: a bucket policy that lets this one distribution, and nothing
  else, read (`s3:GetObject`) the files.

## Things worth knowing

- `yarn build:app:docker` is Excalidraw's own build for self-hosting (their
  Dockerfile runs it). The plain `yarn build` is the one for excalidraw.com: it
  switches on their analytics.
- Drawings stay in your browser. Live collaboration and share links still talk
  to Excalidraw's public servers, as in any self-hosted copy; point the
  `VITE_APP_*` variables in `.env.production` elsewhere to change that.
- The first deploy is slow because a new CloudFront distribution takes a few
  minutes to roll out worldwide. Later uploads are just the `aws s3 sync`.
- CloudFront caches. After you upload a new build, tell it to fetch fresh
  copies: `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"`.
- The address is https on a `cloudfront.net` name. Your own domain needs a
  certificate (ACM, in us-east-1) and an `Aliases` entry on the distribution.
- Opening the bucket's own S3 address gives *Access Denied*. That is the point.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep02-excalidraw-cloudfront/cleanup.sh
bash cleanup.sh my-excalidraw
```

It empties the bucket, deletes the stack and waits until it is gone. A bucket
must be empty before CloudFormation can delete it, and switching a CloudFront
distribution off takes a few minutes.

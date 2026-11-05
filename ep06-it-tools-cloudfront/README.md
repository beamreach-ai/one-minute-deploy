# ep.06 · IT-Tools on S3 + CloudFront, with CloudFormation

Build [IT-Tools](https://github.com/CorentinTh/it-tools) (a collection of handy
online tools for developers, by Corentin Thomasset, GPL-3.0) from source and
serve it over **https** from a **private** S3 bucket behind CloudFront: one
template, five commands. In the video the commands took 11 minutes in total,
seven for the build (on a busy laptop) and just under four for CloudFront.

## Deploy

You need Node 18 or newer and [pnpm](https://pnpm.io) (`corepack enable` gives
you pnpm if you only have Node). S3 bucket names are global, so pick your own.
Replace `my-it-tools` below with the name you choose.

```bash
# 1 · get the code and the template
git clone --depth 1 \
  https://github.com/CorentinTh/it-tools
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep06-it-tools-cloudfront/site.yaml

# 2 · install the dependencies and build the app (a few minutes)
(cd it-tools && pnpm install && pnpm build)

# 3 · name your bucket: change CHANGE-ME to my-it-tools
nano site.yaml

# 4 · create the bucket and the CloudFront distribution (about 4 minutes)
aws cloudformation deploy \
  --stack-name it-tools \
  --template-file site.yaml

# 5 · upload the build
aws s3 sync it-tools/dist s3://my-it-tools
```

Get the address and open it:

```bash
aws cloudformation describe-stacks --stack-name it-tools \
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
  caches them at the edge. Its `CustomErrorResponses` answer any path that is
  not a file with `index.html` (see below).
- **`CdnRead`**: a bucket policy that lets this one distribution, and nothing
  else, read (`s3:GetObject`) the files.

## Things worth knowing

- IT-Tools is a single-page app: `/uuid-generator` is not a file in the
  bucket, the page's own router draws it. Without the `CustomErrorResponses`
  block a reload or a shared link to a tool would get *Access Denied*. A private
  bucket answers 403 for a missing file (not 404), which is why both codes are
  mapped.
- The flip side: a mistyped file name now returns the app instead of an error.
- The first deploy is slow because a new CloudFront distribution takes a few
  minutes to roll out worldwide. Later uploads are just the `aws s3 sync`.
- CloudFront caches. After you upload a new build, tell it to fetch fresh
  copies: `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"`.
- The address is https on a `cloudfront.net` name. Your own domain needs a
  certificate (ACM, in us-east-1) and an `Aliases` entry on the distribution.
- Everything the tools do happens in your browser; nothing you type is sent to
  a server.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep06-it-tools-cloudfront/cleanup.sh
bash cleanup.sh my-it-tools
```

It empties the bucket, deletes the stack and waits until it is gone. A bucket
must be empty before CloudFormation can delete it, and switching a CloudFront
distribution off takes a few minutes.

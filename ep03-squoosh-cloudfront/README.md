# ep.03 · Squoosh on S3 + CloudFront, with CloudFormation

Build [Squoosh](https://github.com/GoogleChromeLabs/squoosh) (the in-browser
image compressor, by Google Chrome Labs, Apache-2.0) from source and serve it
over **https** from a **private** S3 bucket behind CloudFront: one template,
five commands. In the video the commands took 4 min 42 s in total, most of it
waiting for CloudFront.

## Deploy

You need Node and npm (the repo pins Node 20 in `.nvmrc`; the video used
Node 24). S3 bucket names are global, so pick your own. Replace `my-squoosh`
below with the name you choose.

```bash
# 1 · get the code and the template
git clone --depth 1 \
  https://github.com/GoogleChromeLabs/squoosh
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep03-squoosh-cloudfront/site.yaml

# 2 · install the dependencies and build the app (about a minute)
(cd squoosh && npm install && npm run build)

# 3 · name your bucket: change CHANGE-ME to my-squoosh
nano site.yaml

# 4 · create the bucket and the CloudFront distribution (about 4 minutes)
aws cloudformation deploy \
  --stack-name squoosh \
  --template-file site.yaml

# 5 · upload the build
aws s3 sync squoosh/build s3://my-squoosh
```

Get the address and open it:

```bash
aws cloudformation describe-stacks --stack-name squoosh \
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
- **`Utf8`**: a tiny CloudFront Function that adds `charset=utf-8` to the
  page's `Content-Type` (see below).
- **`CdnRead`**: a bucket policy that lets this one distribution, and nothing
  else, read (`s3:GetObject`) the files.

## Things worth knowing

- Squoosh's `index.html` does not declare its character set, and S3 does not
  add one to the `Content-Type`. Without it the arrows next to
  the savings (`↓97%`) show up as `â†“`. The `Utf8` function fixes that at the
  edge. The other way is to upload that one file again with
  `aws s3 cp squoosh/build/index.html s3://my-squoosh --content-type "text/html; charset=utf-8"`.
- Images never leave your browser: the codecs run there as WebAssembly. That
  is why a bucket and a CDN are all the "server" it needs.
- The build also writes `_headers` and `_redirects`. They are instructions for
  Netlify; S3 just stores them as two small files. One thing they would add is
  the pair of headers that lets the codecs use several threads, so this copy
  encodes on one thread.
- The build prints `Unable to determine site origin, defaulting to
  https://squoosh.app`. That only affects the link-preview tags.
- The first deploy is slow because a new CloudFront distribution takes a few
  minutes to roll out worldwide. Later uploads are just the `aws s3 sync`.
- CloudFront caches. After you upload a new build, tell it to fetch fresh
  copies: `aws cloudfront create-invalidation --distribution-id <id> --paths "/*"`.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep03-squoosh-cloudfront/cleanup.sh
bash cleanup.sh my-squoosh
```

It empties the bucket, deletes the stack and waits until it is gone. A bucket
must be empty before CloudFormation can delete it, and switching a CloudFront
distribution off takes a few minutes.

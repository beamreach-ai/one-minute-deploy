# ep.01 · 2048 on an S3 bucket, with CloudFormation

Put the game [2048](https://github.com/gabrielecirulli/2048) (by Gabriele
Cirulli, MIT) on the internet as a static website: one S3 bucket, one bucket
policy, four commands. In the video the commands took 47 seconds in total.

## Deploy

S3 bucket names are global, so pick your own. Replace `my-2048-game` below with
the name you choose.

```bash
# 1 · get the code and the template
git clone https://github.com/gabrielecirulli/2048
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep01-2048-s3/site.yaml

# 2 · name your bucket: change CHANGE-ME to my-2048-game
nano site.yaml

# 3 · create the bucket (about 40 s)
aws cloudformation deploy \
  --stack-name play-2048 \
  --template-file site.yaml

# 4 · upload the site
aws s3 sync 2048 s3://my-2048-game \
  --exclude ".git*"
```

Get the address and open it:

```bash
aws cloudformation describe-stacks --stack-name play-2048 \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

It looks like `http://my-2048-game.s3-website-<region>.amazonaws.com`.

## What the template creates

[`site.yaml`](site.yaml) is the whole infrastructure:

- **`Site`**: an S3 bucket with static website hosting on, serving
  `index.html`. Its public-access block is relaxed so that a public policy is
  allowed.
- **`PublicRead`**: a bucket policy that lets anyone read (`s3:GetObject`) the
  files. Nobody but you can write or list.

## Things worth knowing

- `--exclude ".git*"` matters. Without it the upload would publish the repo's
  `.git` folder to the world.
- S3 website addresses are **http only**. For https and your own domain, put
  CloudFront in front (a later episode).
- If the deploy fails on the bucket policy, your account or organisation blocks
  public buckets (S3 → *Block Public Access settings for this account*).

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep01-2048-s3/cleanup.sh
bash cleanup.sh my-2048-game
```

It empties the bucket, deletes the stack and waits until it is gone. A bucket
must be empty before CloudFormation can delete it.

# ep.04 · draw.io on an S3 bucket, with CloudFormation

Run your own copy of the diagram editor
[draw.io](https://github.com/jgraph/drawio) (by JGraph, Apache-2.0) as a static
website: one S3 bucket, one bucket policy, four commands. The editor is plain
files, and the repo ships them ready-built in `src/main/webapp`, so there is
nothing to compile. In the video the commands took 3 min 52 s in total, most of
it the upload.

## Deploy

S3 bucket names are global, so pick your own. Replace `my-drawio` below with
the name you choose.

```bash
# 1 · get the code (a shallow clone: the full history is far bigger) and the template
git clone --depth 1 \
  https://github.com/jgraph/drawio
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep04-drawio-s3/site.yaml

# 2 · name your bucket: change CHANGE-ME to my-drawio
nano site.yaml

# 3 · create the bucket (about a minute)
aws cloudformation deploy \
  --stack-name drawio \
  --template-file site.yaml

# 4 · upload the app (about 3,000 files, 107 MB: a few minutes)
aws s3 sync drawio/src/main/webapp \
  s3://my-drawio \
  --exclude "*-INF/*"
```

Get the address and open it:

```bash
aws cloudformation describe-stacks --stack-name drawio \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

It looks like `http://my-drawio.s3-website-<region>.amazonaws.com`. The editor
opens on a blank diagram. In a narrow window the shape palette starts closed:
open it with the first toolbar button → *Shapes*.

## What the template creates

[`site.yaml`](site.yaml) is the whole infrastructure, the same template as
[ep.01](../ep01-2048-s3/):

- **`Site`**: an S3 bucket with static website hosting on, serving
  `index.html`. Its public-access block is relaxed so that a public policy is
  allowed.
- **`PublicRead`**: a bucket policy that lets anyone read (`s3:GetObject`) the
  files. Nobody but you can write or list.

## Things worth knowing

- `--exclude "*-INF/*"` matters. `WEB-INF` and `META-INF` are the Java server
  half of the project (jars, servlet config). A static site does not use them,
  and in our run S3 refused every one of those uploads with a 404, which makes
  `aws s3 sync` exit with an error.
- Nothing you draw is stored in the bucket: it only serves the editor's files,
  and visitors cannot write to it. The red "Unsaved changes. Click here to
  save." in the menu bar is the editor reminding you to save the diagram
  yourself (*File* menu).
- S3 website addresses are **http only**. For https and your own domain, put
  CloudFront in front (a later episode).
- If the deploy fails on the bucket policy, your account or organisation blocks
  public buckets (S3 → *Block Public Access settings for this account*).

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep04-drawio-s3/cleanup.sh
bash cleanup.sh my-drawio
```

It empties the bucket, deletes the stack and waits until it is gone. A bucket
must be empty before CloudFormation can delete it.

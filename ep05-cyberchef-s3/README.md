# ep.05 · CyberChef on an S3 bucket, from its release zip

[CyberChef](https://github.com/gchq/CyberChef) (by GCHQ, Apache-2.0) is a
browser toolbox for encoding, decoding, hashing and decrypting. It is a pure
static site, and every release ships as a ready-built zip, so there is nothing
to build. In the video the commands took 58 seconds in total.

## Deploy

S3 bucket names are global, so pick your own. Replace `my-cyberchef` below.

```bash
# 1 · get the latest release (GitHub CLI; or download the zip from the releases page)
gh release download -R gchq/CyberChef \
  -p "*.zip"

# 2 · unpack it; the main page is named after the version, S3 wants index.html
unzip -q CyberChef*.zip -d chef && \
  mv chef/CyberChef*.html chef/index.html

# 3 · get the template and name your bucket: change CHANGE-ME to my-cyberchef
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep05-cyberchef-s3/site.yaml
nano site.yaml

# 4 · create the bucket (about 40 s)
aws cloudformation deploy \
  --stack-name cyberchef \
  --template-file site.yaml

# 5 · upload the site (about 80 MB)
aws s3 sync chef s3://my-cyberchef
```

Get the address and open it:

```bash
aws cloudformation describe-stacks --stack-name cyberchef \
  --query 'Stacks[0].Outputs[0].OutputValue' --output text
```

The template is the same one as [ep.01](../ep01-2048-s3/): one public-read
bucket with static website hosting. The address is **http only**.

## Clean up

```bash
curl -O https://raw.githubusercontent.com/beamreach-ai/one-minute-deploy/main/ep05-cyberchef-s3/cleanup.sh
bash cleanup.sh my-cyberchef
```

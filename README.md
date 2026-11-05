# 1-Minute Deploy

Templates and exact commands behind the *1-Minute Deploy* short-video series:
each episode takes a useful open-source app and puts it on the cloud for real,
in about a minute of commands.

Every episode folder is self-contained: the infrastructure template, the
commands shown in the video, and a cleanup script.

| # | App | Where | How | Folder |
|---|-----|-------|-----|--------|
| 01 | [2048](https://github.com/gabrielecirulli/2048) (the game) | AWS S3 static website | CloudFormation | [`ep01-2048-s3/`](ep01-2048-s3/) |

AWS only for now; Azure and GCP episodes will follow.

## Before you run anything

- You need your own cloud account and credentials. For AWS: the
  [AWS CLI](https://aws.amazon.com/cli/) with a configured profile
  (`aws configure`), then `export AWS_PROFILE=<your-profile>`.
- These deploys create **public** resources in **your** account. They cost
  cents at most, but only if you delete them afterwards: every episode has a
  `cleanup.sh`. Run it when you are done.
- The apps belong to their authors. Each episode links the upstream repo and
  its licence; nothing is copied here.

## How the videos are made

[`reel/`](reel/) holds the tooling. The commands in a video are run for real
and their output and timings are recorded; the video is then drawn from that
recording, with long waits shortened and labelled with the real elapsed time.

```bash
AWS_PROFILE=<profile> reel/capture.sh work-ep01   # real deploy + gameplay capture (site stays up)
ep01-2048-s3/cleanup.sh <bucket>                  # tear it down
reel/build.sh work-ep01                           # picture, 5 soundtracks, reels, review page
```

Needs Python 3 with `numpy`, `pillow` and `playwright`, plus `ffmpeg`. Fonts
and the editor screen assume macOS.

Sister series: [1-Minute Hacking](https://github.com/beamreach-ai/one-minute-hacking).

Built by [Beamreach](https://beamreach.ai). MIT licensed.

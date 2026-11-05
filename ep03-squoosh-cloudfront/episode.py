# ep.03 · Squoosh built from source, on a private S3 bucket behind CloudFront.
EP = {
    "num": 3, "slug": "ep03_squoosh_cloudfront",
    "title": {"app": "Squoosh", "sub": "the in-browser image compressor", "target": "S3 + CloudFront",
              "how": "with CloudFormation · AWS"},
    "credit": "app by GoogleChromeLabs",
    "files": ["site.yaml"],
    "steps": [
        {"caption": "get the code", "out": "clone",
         "cmd": ["git clone --depth 1 \\", "  https://github.com/GoogleChromeLabs/squoosh"],
         "run": "git clone --depth 1 --progress https://github.com/GoogleChromeLabs/squoosh",
         "progress": True, "rules": [["done.", "dim"], ["remote:", "dim"]], "frames": 12},
        {"caption": "install + build", "out": "build",
         "cmd": ["(cd squoosh && npm install && npm run build)"],
         "tail": 9, "frames": 36, "rules": [["created", "green"], ["Warning", "dim"], ["trace-deprecation", "dim"], ["rowserslist", "dim"]]},
        {"caption": "name your bucket", "cmd": ["nano site.yaml"],
         "edit": {"file": "site.yaml", "find": "CHANGE-ME", "replace": "beamreach-squoosh"}},
        {"caption": "bucket + CloudFront", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name squoosh \\", "  --template-file site.yaml"],
         "frames": 36, "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
        {"caption": "upload the build", "out": "sync",
         "cmd": ["aws s3 sync squoosh/build s3://beamreach-squoosh"],
         "filter": r"upload: [^\r\n]*?(?=Completed|\r|\n|$)", "rules": [["index.html", "cyan"]], "tail": 30, "frames": 30},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name squoosh "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the CloudFront URL", "live": "your own Squoosh, on https",
                "seconds": 8, "start": 0.3, "hook_at": 5.1, "width": 640},
}

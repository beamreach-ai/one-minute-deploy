# ep.04 · draw.io on an S3 static website, with CloudFormation.
EP = {
    "num": 4, "slug": "ep04_drawio_s3",
    "title": {"app": "draw.io", "sub": "diagram editor", "target": "S3 bucket", "how": "with CloudFormation · AWS"},
    "credit": "app by JGraph",
    "files": ["site.yaml"],
    "steps": [
        {"caption": "get the code", "out": "clone",
         "cmd": ["git clone --depth 1 \\", "  https://github.com/jgraph/drawio"],
         "run": "git clone --progress --depth 1 https://github.com/jgraph/drawio",
         "progress": True, "rules": [["done.", "dim"], ["remote:", "dim"]], "frames": 26},
        {"caption": "name your bucket", "cmd": ["nano site.yaml"],
         "edit": {"file": "site.yaml", "find": "CHANGE-ME", "replace": "beamreach-drawio"}},
        {"caption": "create the bucket", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name drawio \\", "  --template-file site.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
        {"caption": "upload the app", "out": "sync",
         "cmd": ["aws s3 sync drawio/src/main/webapp \\", "  s3://beamreach-drawio \\", '  --exclude "*-INF/*"'],
         "filter": r"upload: [^\r\n]*?(?=Completed|\r|\n|$)", "rules": [["index.html", "cyan"]], "tail": 30, "frames": 70},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name drawio "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the bucket's public URL", "live": "your own draw.io",
                "seconds": 8, "start": 0.1, "hook_at": 5.4, "width": 720},
}

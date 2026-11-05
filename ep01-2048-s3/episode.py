# ep.01 · 2048 on an S3 static website, with CloudFormation.
EP = {
    "num": 1, "slug": "ep01_2048_s3",
    "title": {"app": "2048", "sub": "the game", "target": "S3 bucket", "how": "with CloudFormation · AWS"},
    "credit": "app by gabrielecirulli",
    "files": ["site.yaml"],
    "steps": [
        {"caption": "get the code", "out": "clone",
         "cmd": ["git clone https://github.com/gabrielecirulli/2048"],
         "run": "git clone --progress https://github.com/gabrielecirulli/2048",
         "progress": True, "rules": [["done.", "dim"], ["remote:", "dim"]], "frames": 26},
        {"caption": "name your bucket", "cmd": ["nano site.yaml"],
         "edit": {"file": "site.yaml", "find": "CHANGE-ME", "replace": "beamreach-2048"}},
        {"caption": "create the bucket", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name play-2048 \\", "  --template-file site.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
        {"caption": "upload the site", "out": "sync",
         "cmd": ["aws s3 sync 2048 s3://beamreach-2048 \\", '  --exclude ".git*"'],
         "filter": r"upload: [^\r\n]*?(?=Completed|\r|\n|$)", "rules": [["index.html", "cyan"]], "frames": 38},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name play-2048 "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the bucket's public URL", "live": "it's live — and it plays",
                "seconds": 8, "hook_at": 10.5, "width": 540},
}

# ep.06 · IT-Tools built from source, on a private S3 bucket behind CloudFront.
EP = {
    "num": 6, "slug": "ep06_it_tools_cloudfront",
    "title": {"app": "IT-Tools", "sub": "handy online tools for developers", "target": "S3 + CloudFront",
              "how": "with CloudFormation · AWS"},
    "credit": "app by CorentinTh",
    "files": ["site.yaml"],
    "steps": [
        {"caption": "get the code", "out": "clone",
         "cmd": ["git clone --depth 1 \\", "  https://github.com/CorentinTh/it-tools"],
         "run": "git clone --depth 1 --progress https://github.com/CorentinTh/it-tools",
         "progress": True, "rules": [["done.", "dim"], ["remote:", "dim"]], "frames": 12},
        {"caption": "install + build", "out": "build",
         "cmd": ["(cd it-tools && pnpm install && pnpm build)"],
         "tail": 10, "frames": 36, "rules": [["built in", "green"], ["warnings", "amber"]]},
        {"caption": "name your bucket", "cmd": ["nano site.yaml"],
         "edit": {"file": "site.yaml", "find": "CHANGE-ME", "replace": "beamreach-it-tools"}},
        {"caption": "bucket + CloudFront", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name it-tools \\", "  --template-file site.yaml"],
         "frames": 36, "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
        {"caption": "upload the build", "out": "sync",
         "cmd": ["aws s3 sync it-tools/dist s3://beamreach-it-tools"],
         "filter": r"upload: [^\r\n]*?(?=Completed|\r|\n|$)", "rules": [["index.html", "cyan"]], "tail": 30, "frames": 30},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name it-tools "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the CloudFront URL", "live": "your own toolbox, on https",
                "seconds": 8, "hook_at": 5.1, "width": 540},
}

# ep.02 · Excalidraw built from source, on a private S3 bucket behind CloudFront.
EP = {
    "num": 2, "slug": "ep02_excalidraw_cloudfront",
    "title": {"app": "Excalidraw", "sub": "the hand-drawn whiteboard", "target": "S3 + CloudFront",
              "how": "with CloudFormation · AWS"},
    "credit": "app by excalidraw",
    "env": {"COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"},
    "files": ["site.yaml"],
    "steps": [
        {"caption": "get the code", "out": "clone",
         "cmd": ["git clone --depth 1 \\", "  https://github.com/excalidraw/excalidraw"],
         "run": "git clone --depth 1 --progress https://github.com/excalidraw/excalidraw",
         "progress": True, "rules": [["done.", "dim"], ["remote:", "dim"]], "frames": 12},
        # yarn is launched through corepack (it ships with Node); same yarn, same commands
        {"caption": "install + build", "out": "build",
         "cmd": ["(cd excalidraw && yarn && yarn build:app:docker)"],
         "run": "(cd excalidraw && corepack yarn && corepack yarn build:app:docker)",
         "tail": 10, "frames": 36, "rules": [["built in", "green"], ["Done in", "green"]]},
        {"caption": "name your bucket", "cmd": ["nano site.yaml"],
         "edit": {"file": "site.yaml", "find": "CHANGE-ME", "replace": "beamreach-excalidraw"}},
        {"caption": "bucket + CloudFront", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name excalidraw \\", "  --template-file site.yaml"],
         "frames": 36, "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
        {"caption": "upload the build", "out": "sync",
         "cmd": ["aws s3 sync excalidraw/excalidraw-app/build \\", "  s3://beamreach-excalidraw"],
         "filter": r"upload: [^\r\n]*?(?=Completed|\r|\n|$)", "rules": [["index.html", "cyan"]], "tail": 30, "frames": 30},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name excalidraw "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the CloudFront URL", "live": "your own Excalidraw, on https",
                "seconds": 8, "hook_at": 6.5, "width": 540},
}

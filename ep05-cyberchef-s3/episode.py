# ep.05 · CyberChef on an S3 static website, from its release zip.
EP = {
    "num": 5, "slug": "ep05_cyberchef_s3",
    "title": {"app": "CyberChef", "sub": "encode, decode, decrypt: 300+ tools", "target": "S3 bucket",
              "how": "from a release zip · AWS"},
    "credit": "app by GCHQ",
    "files": ["site.yaml"],
    "steps": [
        {"caption": "get the latest release", "out": "download",
         "cmd": ["gh release download -R gchq/CyberChef \\", '  -p "*.zip"']},
        {"caption": "unpack it", "out": "unzip",
         "cmd": ["unzip -q CyberChef*.zip -d chef && \\", "  mv chef/CyberChef*.html chef/index.html"]},
        {"caption": "name your bucket", "cmd": ["nano site.yaml"],
         "edit": {"file": "site.yaml", "find": "CHANGE-ME", "replace": "beamreach-cyberchef"}},
        {"caption": "create the bucket", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name cyberchef \\", "  --template-file site.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
        {"caption": "upload the site", "out": "sync", "cmd": ["aws s3 sync chef s3://beamreach-cyberchef"],
         "filter": r"upload: [^\r\n]*?(?=Completed|\r|\n|$)", "rules": [["index.html", "cyan"]], "tail": 30, "frames": 50},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name cyberchef "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the bucket's public URL", "live": "your own CyberChef", "seconds": 8, "width": 860},
}

# ep.09 · Uptime Kuma on one small EC2 instance, with CloudFormation.
EP = {
    "num": 9, "slug": "ep09_uptime_kuma_ec2",
    "title": {"app": "Uptime Kuma", "sub": "your own uptime monitor", "target": "EC2 instance",
              "how": "with CloudFormation · AWS"},
    "credit": "app by louislam",
    "files": ["kuma.yaml"],
    "steps": [
        {"caption": "one template: network + server", "out": "resources",
         "cmd": ["grep Type: kuma.yaml"], "rules": [["CHANGE-ME", "amber"], ["Instance", "cyan"]], "frames": 20},
        {"caption": "pick the server size", "cmd": ["nano kuma.yaml"],
         "edit": {"file": "kuma.yaml", "find": "CHANGE-ME", "replace": "t3.micro"}},
        {"caption": "create it, boot it, start the app", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name kuma \\", "  --template-file kuma.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name kuma "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text",
             "ready_timeout": 600},
    "browser": {"open": "open the server's address", "live": "your own uptime monitor",
                "seconds": 8, "hook_at": 5.9, "width": 540},
}

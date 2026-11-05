# ep.12 · PairDrop on one EC2 instance (Docker from user-data), with CloudFormation.
EP = {
    "num": 12, "slug": "ep12_pairdrop_ec2",
    "title": {"app": "PairDrop", "sub": "send files between your devices", "target": "EC2 instance",
              "how": "with CloudFormation · AWS"},
    "credit": "app by schlagmichdoch",
    "files": ["pairdrop.yaml"],
    "steps": [
        {"caption": "what the template creates", "out": "grep",
         "cmd": ['grep "Type: AWS::EC2" pairdrop.yaml'], "rules": [["Instance", "cyan"]], "frames": 22},
        {"caption": "switch on the relay fallback", "cmd": ["nano pairdrop.yaml"],
         "edit": {"file": "pairdrop.yaml", "find": "false", "replace": "true"}},
        {"caption": "create it all", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name pairdrop \\", "  --template-file pairdrop.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name pairdrop "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text"},
    "browser": {"open": "open the server's public address", "live": "your own PairDrop",
                "seconds": 8, "start": 0.1, "hook_at": 4.0, "width": 540},
}

# ep.10 · Actual Budget on ECS Fargate, behind a load balancer, with https from CloudFront.
EP = {
    "num": 10, "slug": "ep10_actual_fargate",
    "title": {"app": "Actual Budget", "sub": "your own budgeting app", "target": "ECS Fargate",
              "how": "with CloudFormation · AWS"},
    "credit": "app by Actual Budget",
    "files": ["actual.yaml"],
    "steps": [
        {"caption": "one template: container + https", "out": "resources",
         "cmd": ["grep AWS:: actual.yaml"], "rules": [["ECS", "cyan"], ["CloudFront", "green"]], "frames": 30},
        {"caption": "pick the version", "cmd": ["nano actual.yaml"],
         "edit": {"file": "actual.yaml", "find": "CHANGE-ME", "replace": "latest"}},
        {"caption": "create it all (https takes a while)", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name actual \\", "  --template-file actual.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
    ],
    "live": {"url_cmd": "aws cloudformation describe-stacks --stack-name actual "
                        "--query 'Stacks[0].Outputs[0].OutputValue' --output text",
             "ready_timeout": 900},
    "browser": {"open": "open the https address", "live": "your own budgeting app",
                "seconds": 8, "start": 0.2, "hook_at": 7.0, "width": 540},
}

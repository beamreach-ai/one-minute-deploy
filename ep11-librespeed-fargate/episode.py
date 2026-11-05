# ep.11 · LibreSpeed on ECS Fargate (one task, public IP, no load balancer).
EP = {
    "num": 11, "slug": "ep11_librespeed_fargate",
    "title": {"app": "LibreSpeed", "sub": "your own speed test", "target": "ECS Fargate",
              "how": "with CloudFormation · AWS"},
    "credit": "app by LibreSpeed",
    "files": ["speedtest.yaml"],
    "steps": [
        {"caption": "one template: network + container", "out": "resources",
         "cmd": ["grep Type: speedtest.yaml"], "rules": [["ECS", "cyan"]], "frames": 22},
        {"caption": "name your speed test", "cmd": ["nano speedtest.yaml"],
         "edit": {"file": "speedtest.yaml", "find": "CHANGE-ME", "replace": "Beamreach Speed Test"}},
        {"caption": "create it and start the container", "out": "deploy",
         "cmd": ["aws cloudformation deploy \\", "  --stack-name speedtest \\", "  --template-file speedtest.yaml"],
         "rules": [["Successfully", "green"], ["Waiting", "dim"]]},
    ],
    # the task's public IP is not a stack output: task -> network interface -> address
    "live": {"url_cmd": "T=$(aws ecs list-tasks --cluster speedtest --query 'taskArns[0]' --output text); "
                        "E=$(aws ecs describe-tasks --cluster speedtest --tasks $T --output text --query "
                        "\"tasks[0].attachments[0].details[?name=='networkInterfaceId'].value\"); "
                        "echo http://$(aws ec2 describe-network-interfaces --network-interface-ids $E "
                        "--query 'NetworkInterfaces[0].Association.PublicIp' --output text)",
             "ready_timeout": 600},
    "browser": {"open": "open the task's public address", "live": "testing against your own server",
                "seconds": 8, "start": 0.0, "hook_at": 9.6, "width": 540},
}

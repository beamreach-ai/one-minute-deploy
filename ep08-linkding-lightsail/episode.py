# ep.08 · linkding (bookmark manager) from its public image, on a Lightsail container service.
EP = {
    "num": 8, "slug": "ep08_linkding_lightsail",
    "title": {"app": "linkding", "sub": "your own bookmark manager", "target": "Lightsail container",
              "how": "with the AWS CLI"},
    "credit": "app by sissbruecker",
    "term_title": "aws: public-demo · us-west-2 — zsh",
    "env": {"AWS_REGION": "us-west-2", "AWS_DEFAULT_REGION": "us-west-2"},
    "files": ["linkding.yaml"],
    "steps": [
        {"caption": "create a container service", "out": "service",
         "cmd": ["aws lightsail create-container-service \\", "  --service-name linkding --power nano --scale 1"],
         "filter": r'"(?:containerServiceName|power|state|scale)": [^\n]*',
         "rules": [["PENDING", "amber"]], "frames": 16},
        {"caption": "set your password", "cmd": ["nano linkding.yaml"],
         "edit": {"file": "linkding.yaml", "find": "CHANGE-ME", "replace": "throwaway-123"}},
        {"caption": "deploy the container", "out": "deploy",
         "cmd": ["aws lightsail \\", "  create-container-service-deployment \\", "  --cli-input-yaml file://linkding.yaml"],
         "filter": r'"(?:state|image|containerPort)": [^\n]*',
         "rules": [["PENDING", "amber"], ["ACTIVATING", "amber"], ["image", "cyan"]], "frames": 16},
        {"caption": "wait until it is running", "out": "wait", "hide_output": True,
         "cmd": ["until aws lightsail get-container-services \\", "  --service-name linkding | grep -q RUNNING; \\",
                 "  do sleep 5; done"]},
    ],
    "live": {"url_cmd": "aws lightsail get-container-services --service-name linkding "
                        "--query 'containerServices[0].url' --output text",
             "ready_timeout": 1200},
    "browser": {"open": "open the service's https URL", "live": "your own bookmarks, on https",
                "seconds": 8, "start": 0.06, "width": 540,       # start: skip the blank first frame
                "hook_at": 99},                                   # past the end = the last second
}

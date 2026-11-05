# ep.07 · Memos (self-hosted notes) from its public image, on a Lightsail container service.
EP = {
    "num": 7, "slug": "ep07_memos_lightsail",
    "title": {"app": "Memos", "sub": "your own notes app", "target": "Lightsail container",
              "how": "with the AWS CLI"},
    "credit": "app by usememos",
    "term_title": "aws: public-demo · us-west-2 — zsh",
    "env": {"AWS_REGION": "us-west-2", "AWS_DEFAULT_REGION": "us-west-2"},
    "files": ["memos.yaml"],
    "steps": [
        {"caption": "create a container service", "out": "service",
         "cmd": ["aws lightsail create-container-service \\", "  --service-name memos --power nano --scale 1"],
         "filter": r'"(?:containerServiceName|power|state|scale)": [^\n]*',
         "rules": [["PENDING", "amber"]], "frames": 16},
        {"caption": "pick the image", "cmd": ["nano memos.yaml"],
         "edit": {"file": "memos.yaml", "find": "CHANGE-ME", "replace": "neosmemo/memos:stable"}},
        {"caption": "deploy the container", "out": "deploy",
         "cmd": ["aws lightsail \\", "  create-container-service-deployment \\", "  --cli-input-yaml file://memos.yaml"],
         "filter": r'"(?:state|image|containerPort)": [^\n]*',
         "rules": [["PENDING", "amber"], ["ACTIVATING", "amber"], ["image", "cyan"]], "frames": 16},
        {"caption": "wait until it is running", "out": "wait", "hide_output": True,
         "cmd": ["until aws lightsail get-container-services \\", "  --service-name memos | grep -q RUNNING; \\",
                 "  do sleep 5; done"]},
    ],
    "live": {"url_cmd": "aws lightsail get-container-services --service-name memos "
                        "--query 'containerServices[0].url' --output text",
             "ready_timeout": 1200},
    "browser": {"open": "open the service's https URL", "live": "your own notes, on https",
                "seconds": 8, "start": 0.06, "width": 540,       # start: skip the blank first frame
                "hook_at": 99},                                   # past the end = the last second
}

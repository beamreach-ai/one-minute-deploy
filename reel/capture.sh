#!/bin/bash
# Run ep.01's real commands and record each one's output and wall time, then
# record real gameplay from the live URL. Leaves the site UP: run
# ../ep01-2048-s3/cleanup.sh when you are done.
# Usage: AWS_PROFILE=<profile> capture.sh <work dir>   -> <work>/cap/
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; mkdir -p "$1"; W="$(cd "$1" && pwd)"; PY="${PY:-python3}"
export AWS_PAGER=""
RUN="$W/run"; C="$W/cap"
rm -rf "$RUN"; mkdir -p "$RUN" "$C"; cp "$HERE/../ep01-2048-s3/site.yaml" "$RUN/"
: > "$C/timings.txt"
run(){ # name, command...
  local name=$1; shift
  local t0=$("$PY" -c 'import time;print(time.time())')
  set +e; ( cd "$RUN" && "$@" ) > "$C/$name.raw" 2>&1; local rc=$?; set -e
  local t1=$("$PY" -c 'import time;print(time.time())')
  "$PY" -c "print('%s rc=%d %.1fs' % ('$name', $rc, $t1-$t0))" | tee -a "$C/timings.txt"
  [ $rc -eq 0 ]
}
run clone  git clone --progress https://github.com/gabrielecirulli/2048
sed -i.bak 's/BucketName: CHANGE-ME/BucketName: beamreach-2048/' "$RUN/site.yaml" && rm "$RUN/site.yaml.bak"
run deploy aws cloudformation deploy --stack-name play-2048 --template-file site.yaml
run sync   aws s3 sync 2048 s3://beamreach-2048 --exclude ".git*"
run url    aws cloudformation describe-stacks --stack-name play-2048 --query 'Stacks[0].Outputs[0].OutputValue' --output text
"$PY" "$HERE/game.py" "$(cat "$C/url.raw")" "$C/game" 46

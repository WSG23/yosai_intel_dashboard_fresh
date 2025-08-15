#!/bin/bash
set -euo pipefail

ENV=${DEPLOY_ENV:-staging}
PERCENT=${TRAFFIC_PERCENT:-10}

cat <<YAML | kubectl --context "$ENV" apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: yosai-dashboard
spec:
  hosts:
    - yosai-dashboard
  http:
    - route:
        - destination:
            host: yosai-dashboard
            subset: canary
          weight: ${PERCENT}
        - destination:
            host: yosai-dashboard
            subset: stable
          weight: $((100 - PERCENT))
YAML

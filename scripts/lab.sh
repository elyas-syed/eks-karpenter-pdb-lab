#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export AWS_PAGER=""
export KUBECONFIG="$PWD/lab.kubeconfig"

tf() { terraform -chdir=infra output -raw "$1"; }
k() { kubectl --context karpenter-pdb-lab --request-timeout=20s "$@"; }
die() { echo "$*" >&2; exit 1; }

cluster=$(tf cluster_name)
region=$(tf region)
account=$(tf account_id)
[[ $(aws sts get-caller-identity --query Account --output text) == "$account" ]] ||
  die "AWS credentials do not match the lab account."
expected=$(aws eks describe-cluster --name "$cluster" --region "$region" --query cluster.endpoint --output text)
actual=$(kubectl --context karpenter-pdb-lab config view --minify -o jsonpath='{.clusters[0].cluster.server}')
[[ "$actual" == "$expected" && -n "$actual" ]] || die "Kubeconfig does not point to the Terraform lab cluster."

budget() {
  k patch nodepool pdb-lab --type=merge -p \
    "{\"spec\":{\"disruption\":{\"budgets\":[{\"nodes\":\"$1\"}]}}}"
}

wait_pdb() {
  for ((attempt=0; attempt<30; attempt++)); do
    if k -n pdb-lab get pdb demo -o json |
      jq -e --argjson allowed "$1" '
        .status.observedGeneration == .metadata.generation and
        .status.disruptionsAllowed == $allowed and .status.currentHealthy == 3
      ' >/dev/null; then
      return
    fi
    sleep 2
  done
  die "PDB did not report three healthy pods and $1 allowed disruptions."
}

node_events() {
  k get events -A --field-selector "involvedObject.kind=Node,involvedObject.name=$1" --sort-by=.metadata.creationTimestamp
}

# True while the node exists, has no deletion timestamp and has no Karpenter disruption taint.
node_untouched() {
  k get node "$1" --ignore-not-found -o json | jq -e '
    .metadata.deletionTimestamp == null and
    ([.spec.taints[]?.key] | index("karpenter.sh/disrupted") == null)
  ' >/dev/null
}

wait_blocked() {
  for ((attempt=0; attempt<60; attempt++)); do
    if k get events -A -o json | jq -e --arg node "$1" '
      any(.items[]; .reason == "DisruptionBlocked" and
        (.involvedObject.name == $node or .involvedObject.kind == "NodeClaim") and
        ((.message // "") | contains("pdb-lab/demo")))
    ' >/dev/null; then
      echo "Karpenter reported DisruptionBlocked for pdb-lab/demo."
      return
    fi
    sleep 3
  done
  die "No DisruptionBlocked event naming pdb-lab/demo within 180 seconds."
}

observe() {
  k get nodepool pdb-lab -o jsonpath='{.spec.disruption}{"\n"}'
  k get nodeclaims -l karpenter.sh/nodepool=pdb-lab -o wide
  k get nodes -L karpenter.sh/nodepool,lab.example.com/baseline,node.kubernetes.io/instance-type
  k -n pdb-lab get pods,pdb -o wide
  k -n pdb-lab get endpointslices -l kubernetes.io/service-name=demo -o wide
  if [[ -n "${1:-}" ]]; then node_events "$1"; fi
  k -n kube-system logs -l app.kubernetes.io/name=karpenter -c controller --prefix --since=15m --tail=120
}

case "${1:-}" in
  setup)
    pool=$(k get nodepool pdb-lab --ignore-not-found -o name)
    namespace=$(k get namespace pdb-lab --ignore-not-found -o name)
    [[ -z "$pool" && -z "$namespace" ]] ||
      die "Clean up the previous run before setup."
    k wait --for=condition=Established --timeout=60s \
      crd/nodepools.karpenter.sh crd/nodeclaims.karpenter.sh crd/ec2nodeclasses.karpenter.k8s.aws
    k -n kube-system rollout status deployment/karpenter --timeout=120s
    node_role=$(tf node_role)
    ami=$(tf node_ami)
    sed -e "s/\${CLUSTER_NAME}/$cluster/g" -e "s/\${NODE_ROLE}/$node_role/g" \
      -e "s/\${AMI_ID}/$ami/g" manifests/nodeclass.yaml.tpl | k apply -f -
    k wait --for=condition=Ready ec2nodeclass/pdb-lab --timeout=180s
    k apply -f manifests/nodepool.yaml
    k wait --for=condition=Ready nodepool/pdb-lab --timeout=120s

    k get nodes -l lab.example.com/baseline=true -o json |
      jq -e '
        (.items | length) == 2 and
        ([.items[].metadata.labels["topology.kubernetes.io/zone"]] | unique | length) == 2 and
        all(.items[]; (.spec.unschedulable != true) and
          any(.status.conditions[]; .type == "Ready" and .status == "True"))
      ' >/dev/null || die "Expected two Ready, schedulable baseline nodes in different zones."
    k apply -f manifests/namespace.yaml
    k apply -f manifests/pressure.yaml
    k -n pdb-lab rollout status daemonset/pressure --timeout=180s
    [[ $(k -n pdb-lab get daemonset pressure -o jsonpath='{.status.numberReady}') == 2 ]] ||
      die "Expected one pressure pod per baseline node."
    k apply -f manifests/workload.yaml
    k apply -f manifests/pdb-restrictive.yaml
    k -n pdb-lab rollout status deployment/demo --timeout=360s
    wait_pdb 0
    node=$(k get nodes -l karpenter.sh/nodepool=pdb-lab -o json |
      jq -er '.items | if length == 1 then .[0].metadata.name else error("Expected one Karpenter node") end')
    k wait --for=condition=Ready "node/$node" --timeout=120s
    k -n pdb-lab get pods -l app=pdb-demo -o json |
      jq -e --arg node "$node" '
        [.items[].spec.nodeName] | length == 3 and (unique | length) == 3 and index($node) != null
      ' >/dev/null || die "Expected three demo pods spread across three nodes."
    k -n pdb-lab delete daemonset pressure --timeout=120s
    budget 1
    wait_blocked "$node"
    echo "Restrictive phase. Record this node name for the next steps: $node"
    ;;
  observe)
    observe "${2:-}"
    ;;
  probe-eviction)
    expectation=${2:?Pass blocked or allowed}
    case "$expectation" in blocked|allowed) ;; *) die "Pass blocked or allowed." ;; esac
    node=${3:?Pass the Karpenter node name from setup}
    pod=$(k -n pdb-lab get pods -l app=pdb-demo --field-selector "spec.nodeName=$node" -o json |
      jq -er '[.items[] | select(.metadata.deletionTimestamp == null)] |
        if length == 1 then .[0].metadata.name else error("Expected one demo pod on the candidate") end')
    if result=$(jq -n --arg pod "$pod" '{
        apiVersion: "policy/v1", kind: "Eviction",
        metadata: {name: $pod, namespace: "pdb-lab"},
        deleteOptions: {dryRun: ["All"]}
      }' | k create --raw "/api/v1/namespaces/pdb-lab/pods/$pod/eviction?dryRun=All" -f - 2>&1); then
      [[ "$expectation" == allowed ]] || die "Eviction dry-run unexpectedly succeeded."
      echo "Eviction dry-run admitted. The pod was retained."
    else
      [[ "$expectation" == blocked && "$result" == *TooManyRequests* && "$result" == *"disruption budget"* ]] || die "$result"
      echo "$result"
    fi
    ;;
  budget-control)
    # Keep the same candidate intact while demonstrating the independent node budget.
    node=${2:?Pass the Karpenter node name from setup}
    window=${CONTROL_WINDOW:-180}
    wait_pdb 0
    k get node "$node"
    budget 0
    k apply -f manifests/pdb-permissive.yaml
    wait_pdb 1
    deadline=$((SECONDS + window))
    while :; do
      node_untouched "$node" ||
        die "Karpenter started disrupting $node while the NodePool budget was zero."
      (( SECONDS < deadline )) || break
      sleep 10
    done
    echo "Node $node stayed untouched for the ${window}-second control window."
    observe "$node"
    ;;
  consolidate)
    node=${2:?Pass the Karpenter node name from setup}
    wait_pdb 1
    [[ $(k get nodepool pdb-lab -o jsonpath='{.spec.disruption.budgets[0].nodes}') == 0 ]] ||
      die "Run budget-control before enabling consolidation."
    claim=$(k get nodeclaims -l karpenter.sh/nodepool=pdb-lab -o json |
      jq -er --arg node "$node" '[.items[] | select(.status.nodeName == $node)] |
        if length == 1 then .[0].metadata.name else error("Expected one NodeClaim for candidate") end')
    k get node "$node"
    sample_endpoints() {
      ready=$(k -n pdb-lab get endpointslices -l kubernetes.io/service-name=demo -o json |
        jq '[.items[].endpoints[]? | select(.conditions.ready == true) | .targetRef.uid] | unique | length')
      ready=${ready:-0}
      printf '%s Ready service endpoints: %s\n' "$(date -u +%FT%TZ)" "$ready"
      (( ready >= 2 )) || die "Ready endpoints dropped below the two-replica target."
    }
    k -n pdb-lab apply -f manifests/availability-probe.yaml
    k -n pdb-lab wait --for=condition=Ready pod/availability-probe --timeout=120s
    probe_log=$(k -n pdb-lab logs pod/availability-probe)
    for ((attempt=0; attempt<15; attempt++)); do
      if [[ "$probe_log" == *request_succeeded* ]]; then break; fi
      sleep 2
      probe_log=$(k -n pdb-lab logs pod/availability-probe)
    done
    [[ "$probe_log" == *request_succeeded* && "$probe_log" != *request_failed* ]] ||
      die "Expected successful HTTP probes before consolidation."
    sample_endpoints
    [[ "$ready" == 3 ]] || die "Expected three Ready service endpoints before consolidation."
    budget 1
    restored=$SECONDS
    disrupted_after=""
    removed_after=""
    deadline=$((SECONDS + 480))
    while :; do
      sample_endpoints
      if [[ -z "$disrupted_after" ]] && ! node_untouched "$node"; then
        disrupted_after=$((SECONDS - restored))
      fi
      old_claim=$(k get "nodeclaim/$claim" --ignore-not-found -o name)
      old_node=$(k get "node/$node" --ignore-not-found -o name)
      if [[ -z "$removed_after" && -z "$old_claim" && -z "$old_node" ]]; then
        removed_after=$((SECONDS - restored))
      fi
      if [[ -n "$removed_after" && "$ready" == 3 ]]; then break; fi
      (( SECONDS < deadline )) || die "Consolidation or deployment recovery timed out."
      sleep 2
    done
    window=${CONTROL_WINDOW:-180}
    echo "Seconds from budget restore to first disruption: ${disrupted_after:-unobserved}; to node removal: $removed_after"
    if [[ -n "$disrupted_after" ]] && (( disrupted_after * 2 > window )); then
      echo "WARNING: the ${window}-second control window is less than twice the observed disruption delay." >&2
      echo "Rerun the lab with CONTROL_WINDOW=$((disrupted_after * 3)) before citing the NodePool control result." >&2
    fi
    k -n pdb-lab rollout status deployment/demo --timeout=120s
    k -n pdb-lab get pods -l app=pdb-demo -o json |
      jq -e '[.items[] | select(.metadata.deletionTimestamp == null) | .spec.nodeName] |
        length == 3 and (unique | length) == 2' >/dev/null ||
      die "Expected all three demo replicas on two surviving nodes."
    remaining_claims=$(k get nodeclaims -l karpenter.sh/nodepool=pdb-lab -o name)
    [[ -z "$remaining_claims" ]] || die "Expected zero remaining lab NodeClaims."
    probe_log=$(k -n pdb-lab logs pod/availability-probe --timestamps)
    printf '%s\n' "$probe_log"
    [[ "$probe_log" != *request_failed* ]] || die "At least one synthetic HTTP request failed."
    k -n pdb-lab delete pod availability-probe --timeout=60s
    observe "$node"
    ;;
  cleanup)
    k delete namespace pdb-lab --ignore-not-found --timeout=180s
    k delete nodepool pdb-lab --ignore-not-found --timeout=300s
    for ((attempt=0; attempt<60; attempt++)); do
      remaining_claims=$(k get nodeclaims -l karpenter.sh/nodepool=pdb-lab -o name)
      if [[ -z "$remaining_claims" ]]; then break; fi
      sleep 5
    done
    [[ -z "$remaining_claims" ]] ||
      die "Lab NodeClaims remain after 300 seconds. Keep the controller running and investigate."
    remaining_nodes=$(k get nodes -l karpenter.sh/nodepool=pdb-lab -o name)
    [[ -z "$remaining_nodes" ]] ||
      die "Karpenter nodes remain. Keep the controller running and investigate."
    k delete ec2nodeclass pdb-lab --ignore-not-found --timeout=180s
    ;;
  *)
    die "Usage: $0 {setup|observe [node]|probe-eviction {blocked|allowed} <node>|budget-control <node>|consolidate <node>|cleanup}"
    ;;
esac

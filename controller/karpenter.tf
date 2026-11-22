resource "helm_release" "crds" {
  name       = "karpenter-crd"
  namespace  = local.namespace
  repository = local.repository
  chart      = "karpenter-crd"
  version    = var.karpenter_version
  atomic     = true
}

resource "helm_release" "karpenter" {
  name       = "karpenter"
  namespace  = local.namespace
  repository = local.repository
  chart      = "karpenter"
  version    = var.karpenter_version
  skip_crds  = true
  atomic     = true
  timeout    = 600

  values = [yamlencode({
    replicas       = 2
    nodeSelector   = { "lab.example.com/baseline" = "true" }
    serviceAccount = { name = "karpenter" }
    settings = {
      clusterName       = var.cluster_name
      interruptionQueue = var.interruption_queue
    }
    controller = {
      resources = {
        requests = { cpu = "250m", memory = "512Mi" }
        limits   = { memory = "1Gi" }
      }
    }
  })]

  depends_on = [helm_release.crds]
}

output "karpenter_version" {
  description = "Karpenter chart version installed for both the CRD and controller releases."
  value       = helm_release.karpenter.version
}

output "karpenter_namespace" {
  description = "Namespace that runs the Karpenter controller."
  value       = helm_release.karpenter.namespace
}

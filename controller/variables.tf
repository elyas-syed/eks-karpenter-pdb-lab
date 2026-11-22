variable "kubeconfig" {
  type        = string
  description = "Path to the dedicated lab kubeconfig written by aws eks update-kubeconfig."
}

variable "kube_context" {
  type        = string
  default     = "karpenter-pdb-lab"
  description = "Kubeconfig context alias for the lab cluster. scripts/lab.sh expects the default."
}

variable "cluster_name" {
  type        = string
  description = "EKS cluster name, from the infra root's cluster_name output."
}

variable "interruption_queue" {
  type        = string
  description = "SQS interruption queue name, from the infra root's interruption_queue output."
}

variable "karpenter_version" {
  type        = string
  default     = "1.14.4"
  description = "Version of both Karpenter Helm charts. Check the compatibility matrix for the cluster's Kubernetes version."

  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+$", var.karpenter_version))
    error_message = "Use an exact chart version such as 1.14.4."
  }
}

variable "region" {
  type        = string
  default     = "us-east-2"
  description = "AWS Region for the lab. It must offer EKS 1.36 and the m5.xlarge, m5.large and m5a.large instance types."
}

variable "account_id" {
  type        = string
  description = "AWS account ID the provider may modify. Terraform refuses to run against any other account."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Use a 12-digit AWS account ID."
  }
}

variable "operator_cidr" {
  type        = string
  default     = null
  description = "Optional operator IPv4 /32 for sandbox runs. Null keeps the EKS API private-only."

  validation {
    condition     = var.operator_cidr == null ? true : can(cidrnetmask(var.operator_cidr)) && endswith(var.operator_cidr, "/32")
    error_message = "Use a single public IPv4 address with a /32 suffix."
  }
}

variable "cluster_name" {
  type        = string
  default     = "karpenter-pdb-lab"
  description = "EKS cluster name. Also used for the VPC, Karpenter node role, discovery tags and the Project tag."

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]{0,62}$", var.cluster_name))
    error_message = "Start with a letter and use up to 63 letters, digits or hyphens."
  }
}

variable "kubernetes_version" {
  type        = string
  default     = "1.36"
  description = "EKS Kubernetes minor version. Check the Karpenter compatibility matrix before changing it."

  validation {
    condition     = can(regex("^1\\.[0-9]+$", var.kubernetes_version))
    error_message = "Use a Kubernetes minor version such as 1.36."
  }
}

variable "vpc_cidr" {
  type        = string
  default     = "10.72.0.0/16"
  description = "IPv4 CIDR for the lab VPC. Subnets are carved from it as two /20 private and two /24 public ranges."

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr)) && endswith(var.vpc_cidr, "/16")
    error_message = "Use an IPv4 /16 CIDR."
  }
}

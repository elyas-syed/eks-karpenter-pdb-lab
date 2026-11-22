module "karpenter" {
  source  = "terraform-aws-modules/eks/aws//modules/karpenter"
  version = "21.29.0"

  cluster_name                  = module.eks.cluster_name
  namespace                     = "kube-system"
  node_iam_role_use_name_prefix = false
  node_iam_role_name            = var.cluster_name
  # The generated policy exceeds IAM's managed-policy size limit.
  enable_inline_policy            = true
  create_pod_identity_association = true
  enable_spot_termination         = true
  tags                            = local.tags
}

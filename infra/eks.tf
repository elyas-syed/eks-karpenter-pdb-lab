module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.29.0"

  name                                     = var.cluster_name
  kubernetes_version                       = var.kubernetes_version
  upgrade_policy                           = { support_type = "STANDARD" }
  endpoint_private_access                  = true
  endpoint_public_access                   = var.operator_cidr != null
  endpoint_public_access_cidrs             = var.operator_cidr == null ? [] : [var.operator_cidr]
  enable_cluster_creator_admin_permissions = true
  cloudwatch_log_group_retention_in_days   = 7

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
    eks-pod-identity-agent = { before_compute = true }
  }

  eks_managed_node_groups = {
    for index, az in local.azs : "baseline-${az}" => {
      subnet_ids     = [module.vpc.private_subnets[index]]
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = [local.baseline_instance_type]
      min_size       = 1
      max_size       = 1
      desired_size   = 1
      labels         = { "lab.example.com/placement" = "pdb", "lab.example.com/baseline" = "true" }
    }
  }

  node_security_group_tags = { "karpenter.sh/discovery" = var.cluster_name }
  tags                     = local.tags
}

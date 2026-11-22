module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.0.1"

  name                   = var.cluster_name
  cidr                   = var.vpc_cidr
  azs                    = local.azs
  private_subnets        = local.private_subnets
  public_subnets         = local.public_subnets
  enable_nat_gateway     = true
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  private_subnet_tags    = { "karpenter.sh/discovery" = var.cluster_name }
  tags                   = local.tags
}

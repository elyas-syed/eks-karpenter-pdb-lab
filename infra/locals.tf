locals {
  azs  = slice(data.aws_availability_zones.regional.names, 0, 2)
  tags = { Project = var.cluster_name, Purpose = "temporary-lab" }

  private_subnets = [for index in range(2) : cidrsubnet(var.vpc_cidr, 4, index)]
  public_subnets  = [for index in range(2) : cidrsubnet(var.vpc_cidr, 8, 32 + index)]

  # The pressure DaemonSet in manifests/pressure.yaml is sized for this type.
  # Changing it requires recalculating the CPU reservation.
  baseline_instance_type = "m5.xlarge"
}

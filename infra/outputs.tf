output "cluster_name" {
  description = "EKS cluster name, used by the controller root and scripts/lab.sh."
  value       = module.eks.cluster_name
}

output "region" {
  description = "AWS Region the lab runs in."
  value       = var.region
}

output "account_id" {
  description = "AWS account ID that scripts/lab.sh checks before every command."
  value       = var.account_id
}

output "node_role" {
  description = "IAM role name Karpenter assigns to the nodes it launches."
  value       = module.karpenter.node_iam_role_name
}

output "node_ami" {
  description = "AL2023 AMI ID resolved from SSM and written into the EC2NodeClass. Record it with run evidence."
  value       = nonsensitive(data.aws_ssm_parameter.al2023.value)
}

output "interruption_queue" {
  description = "SQS queue name for Karpenter interruption handling."
  value       = module.karpenter.queue_name
}

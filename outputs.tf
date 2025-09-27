# outputs.tf (у корені проєкту)

output "eks_cluster_name" {
  description = "Назва створеного EKS кластера"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint для доступу до EKS Kubernetes API"
  value       = module.eks.cluster_endpoint
}

output "vpc_id" {
  description = "ID створеної VPC"
  value       = module.vpc.vpc_id
}


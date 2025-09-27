# eks/outputs.tf (Оновлена версія)

output "cluster_name" {
  description = "Назва створеного EKS кластера"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint для доступу до EKS Kubernetes API"
  value       = module.eks.cluster_endpoint
}
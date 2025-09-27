# variables.tf (у корені)
variable "aws_region" {
  description = "Регіон AWS"
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Назва проєкту"
  type        = string
  default     = "ml-infra-stockholm"
}

variable "cluster_name" {
  description = "Назва EKS кластера"
  type        = string
  default     = "ml-cluster-stockholm"
}
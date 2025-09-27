# vpc/variables.tf
variable "aws_region" {
  description = "Регіон AWS"
  type        = string
}

variable "project_name" {
  description = "Назва проєкту для тегування"
  type        = string
}
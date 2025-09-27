# backend.tf (у корені)
terraform {
  backend "s3" {
    bucket = "brem090-tfstate-dev" # <-- Назва бакета
    key    = "root/terraform.tfstate"
    region = "eu-north-1"
  }
}
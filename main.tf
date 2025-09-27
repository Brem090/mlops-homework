# main.tf (у корені)
provider "aws" {
  region = var.aws_region
}

# Створення мережі
module "vpc" {
  source = "./vpc"

  aws_region   = var.aws_region
  project_name = var.project_name
}

# Створення кластера
module "eks" {
  source     = "./eks"
  depends_on = [module.vpc]

  aws_region      = var.aws_region
  cluster_name    = var.cluster_name
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
}

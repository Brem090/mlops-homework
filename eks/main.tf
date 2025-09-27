# eks/main.tf 

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.8.4"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnets

  cluster_endpoint_public_access = true

  enable_cluster_creator_admin_permissions = true


  eks_managed_node_groups = {
    cpu_nodes = {
      min_size       = 1
      max_size       = 2
      desired_size   = 1
      instance_types = ["t3.micro"]
      
      tags = {
        "Name" = "cpu-worker-nodes"
      }
    }

    gpu_nodes = {
      min_size       = 0 
      max_size       = 1
      desired_size   = 0 
      instance_types = ["g4dn.xlarge"]
      ami_type       = "AL2_x86_64_GPU"

      tags = {
        "Name" = "gpu-worker-nodes"
      }
    }
  }
}





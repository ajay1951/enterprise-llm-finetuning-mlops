module "networking" {
  source = "./modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  region             = var.aws_region
  vpc_cidr           = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr
  allowed_ssh_cidr   = var.allowed_ssh_cidr
}

module "database" {
  source = "./modules/database"

  project_name          = var.project_name
  environment           = var.environment
  public_subnet_id      = module.networking.public_subnet_id
  public_subnet_2_id    = module.networking.public_subnet_2_id
  rds_security_group_id = module.networking.rds_security_group_id
  
  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
}

module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment  = var.environment
}

module "registry" {
  source = "./modules/registry"

  project_name = var.project_name
}

module "compute" {
  source = "./modules/compute"

  project_name          = var.project_name
  environment           = var.environment
  public_subnet_id      = module.networking.public_subnet_id
  ec2_security_group_id = module.networking.ec2_security_group_id
  bucket_arn            = module.storage.bucket_arn
  instance_type         = var.ec2_instance_type
}

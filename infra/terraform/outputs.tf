output "ec2_public_ip" {
  value = module.compute.public_ip
}

output "db_endpoint" {
  value = module.database.db_endpoint
}

output "s3_bucket_id" {
  value = module.storage.bucket_id
}

output "ecr_api_repo" {
  value = module.registry.api_repository_url
}

output "ecr_frontend_repo" {
  value = module.registry.frontend_repository_url
}

output "ecr_celery_repo" {
  value = module.registry.celery_repository_url
}

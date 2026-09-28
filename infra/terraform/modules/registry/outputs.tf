output "api_repository_url" {
  value = aws_ecr_repository.api.repository_url
}
output "celery_repository_url" {
  value = aws_ecr_repository.celery.repository_url
}
output "frontend_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

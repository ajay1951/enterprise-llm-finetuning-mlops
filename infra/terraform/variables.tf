variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project Name"
  type        = string
  default     = "forgellm"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH (override in tfvars)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ec2_instance_type" {
  type    = string
  default = "t3.small" # Free tier allows micro, but small is better if we run lots of docker containers
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_name" {
  type    = string
  default = "forgellm"
}

variable "db_username" {
  type    = string
  default = "forgellm_user"
}

variable "db_password" {
  type      = string
  sensitive = true
}

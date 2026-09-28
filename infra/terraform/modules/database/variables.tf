variable "project_name" { type = string }
variable "environment" { type = string }

variable "public_subnet_id" { type = string }
variable "public_subnet_2_id" { type = string }
variable "rds_security_group_id" { type = string }

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

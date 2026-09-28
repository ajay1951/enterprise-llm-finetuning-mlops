variable "project_name" { type = string }
variable "environment" { type = string }

variable "public_subnet_id" { type = string }
variable "ec2_security_group_id" { type = string }
variable "bucket_arn" { type = string }

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

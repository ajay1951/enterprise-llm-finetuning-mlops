resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = [var.public_subnet_id, var.public_subnet_2_id]

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_db_instance" "main" {
  identifier           = "${var.project_name}-db"
  engine               = "postgres"
  engine_version       = "15.4" # Or the latest available in free tier
  instance_class       = var.db_instance_class
  allocated_storage    = 20 # Minimum for free tier
  storage_type         = "gp2"
  
  db_name              = var.db_name
  username             = var.db_username
  password             = var.db_password
  
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_security_group_id]
  
  publicly_accessible  = false
  skip_final_snapshot  = true
  
  # For free tier, no multi_az
  multi_az             = false

  tags = {
    Name        = "${var.project_name}-db"
    Environment = var.environment
  }
}

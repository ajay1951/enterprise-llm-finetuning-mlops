resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "main" {
  bucket = "${var.project_name}-artifacts-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.project_name}-artifacts"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Prefixes (folders)
resource "aws_s3_object" "datasets" {
  bucket = aws_s3_bucket.main.id
  key    = "datasets/"
}

resource "aws_s3_object" "models" {
  bucket = aws_s3_bucket.main.id
  key    = "models/"
}

resource "aws_s3_object" "evaluations" {
  bucket = aws_s3_bucket.main.id
  key    = "evaluations/"
}

resource "aws_s3_object" "mlflow" {
  bucket = aws_s3_bucket.main.id
  key    = "mlflow/"
}

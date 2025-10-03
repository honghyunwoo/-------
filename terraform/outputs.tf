# Terraform Outputs

output "ec2_public_ip" {
  description = "EC2 instance public IP address"
  value       = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  description = "EC2 instance public DNS"
  value       = aws_instance.app.public_dns
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "RDS PostgreSQL address"
  value       = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}

output "s3_bucket_name" {
  description = "S3 bucket name for videos"
  value       = aws_s3_bucket.videos.id
}

output "s3_bucket_domain" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.videos.bucket_regional_domain_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.videos.domain_name
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = "https://${aws_cloudfront_distribution.videos.domain_name}"
}

output "connection_info" {
  description = "Connection information for services"
  value = {
    ssh_command        = "ssh -i ${var.ec2_key_name}.pem ubuntu@${aws_instance.app.public_ip}"
    api_url           = "http://${aws_instance.app.public_ip}:8080"
    webui_url         = "http://${aws_instance.app.public_ip}:8501"
    database_url      = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/owl_studio"
    redis_url         = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
  }
  sensitive = true
}

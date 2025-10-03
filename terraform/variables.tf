# Terraform Variables for Owl Studio Infrastructure

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2" # Seoul
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "owl-studio"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2c"]
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium" # 2 vCPU, 4GB RAM
}

variable "ec2_ami" {
  description = "EC2 AMI ID (Ubuntu 22.04 LTS)"
  type        = string
  default     = "ami-0c9c942bd7bf113a2" # Ubuntu 22.04 LTS in ap-northeast-2
}

variable "ec2_key_name" {
  description = "EC2 SSH key pair name"
  type        = string
}

variable "ssh_allowed_ips" {
  description = "Allowed IP addresses for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"] # 프로덕션에서는 특정 IP로 제한 권장
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # 개발용, 프로덕션은 db.t3.small 이상 권장
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "owl_user"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

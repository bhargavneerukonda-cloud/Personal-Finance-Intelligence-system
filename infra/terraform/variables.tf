variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "finsight"
}

variable "environment" {
  description = "Deployment environment (staging | production)"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be 'staging' or 'production'."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "finsight"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "backend_cpu" {
  description = "Backend ECS task CPU units"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Backend ECS task memory (MB)"
  type        = number
  default     = 1024
}

variable "ml_cpu" {
  description = "ML service ECS task CPU units"
  type        = number
  default     = 1024
}

variable "ml_memory" {
  description = "ML service ECS task memory (MB)"
  type        = number
  default     = 2048
}

variable "backend_desired_count" {
  description = "Number of backend ECS tasks"
  type        = number
  default     = 1
}

variable "ml_desired_count" {
  description = "Number of ML service ECS tasks"
  type        = number
  default     = 1
}

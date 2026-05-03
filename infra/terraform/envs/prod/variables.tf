variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "site_bucket_name" {
  description = "S3 bucket name used for static site hosting and data files"
  type        = string
}

variable "tournament_ids" {
  description = "Comma-separated Challonge tournament IDs/slugs"
  type        = string
}

variable "challonge_user" {
  description = "Challonge API username"
  type        = string
  sensitive   = true
}

variable "challonge_key" {
  description = "Challonge API key"
  type        = string
  sensitive   = true
}

variable "lambda_function_name" {
  description = "Name of the Lambda function that updates /data/*.json"
  type        = string
  default     = "mcchallonge-update-data"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "lambda_handler" {
  description = "Lambda handler entrypoint"
  type        = string
  default     = "mcchallonge.lambda_handlers.update_data.lambda_handler"
}

variable "lambda_package_path" {
  description = "Path to the packaged Lambda zip file"
  type        = string
  default     = "../../../../dist/lambda/update_data.zip"
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_mb" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "data_prefix" {
  description = "S3 prefix used for fixed data files"
  type        = string
  default     = "data"
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for the updater Lambda"
  type        = string
  default     = "rate(5 minutes)"
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

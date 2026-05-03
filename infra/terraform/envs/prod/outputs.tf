output "site_bucket_name" {
  description = "Bucket containing static site and /data payloads"
  value       = aws_s3_bucket.site.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.site.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.site.domain_name
}

output "lambda_function_name" {
  description = "Updater lambda function name"
  value       = aws_lambda_function.data_updater.function_name
}

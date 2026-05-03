# Terraform Infrastructure

This Terraform stack provisions production infrastructure for the serverless dashboard:

- S3 bucket for static site assets and fixed JSON files under `/data`
- CloudFront distribution in front of S3
- Lambda function that updates `data/tournament.json`, `data/participants.json`, `data/matches.json`, and `data/manifest.json`
- EventBridge schedule to trigger Lambda updates
- IAM role and permissions for Lambda execution

## Layout

- `envs/prod`: production environment configuration

## Prerequisites

- Terraform >= 1.6
- AWS credentials with permission to create S3, CloudFront, Lambda, IAM, and EventBridge resources
- A packaged Lambda zip at `dist/lambda/update_data.zip`

## Quick Start

From repository root:

```bash
cd infra/terraform/envs/prod
cp terraform.tfvars.example terraform.tfvars
# Fill in values in terraform.tfvars
terraform init
terraform plan
terraform apply
```

## Remote State Recommendation

Use S3 + DynamoDB for remote state and locking in team environments. Example backend init:

```bash
terraform init \
  -backend-config="bucket=<tf-state-bucket>" \
  -backend-config="key=mcchallonge/prod/terraform.tfstate" \
  -backend-config="region=<aws-region>" \
  -backend-config="dynamodb_table=<tf-lock-table>"
```

## Important Notes

- This stack expects `dist/lambda/update_data.zip` to exist before `terraform apply`.
- Sensitive variables (`challonge_user`, `challonge_key`) are marked sensitive, but still exist in Terraform state.
- For stronger secret handling, migrate these credentials to AWS Secrets Manager and update Lambda code/policy accordingly.

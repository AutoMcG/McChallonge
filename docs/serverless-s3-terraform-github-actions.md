# Serverless Hosting Guide (S3 + CloudFront + Lambda)

This project supports a serverless deployment model where:

- Static pages are served from S3 through CloudFront.
- Frontend reads fixed JSON filenames from `/data`.
- A scheduled Lambda refreshes tournament JSON from Challonge.
- Terraform manages AWS infrastructure.
- GitHub Actions runs CI/CD.

## Fixed Data Contract

Frontend expects these fixed paths:

- `/data/tournament.json`
- `/data/participants.json`
- `/data/matches.json`
- `/data/manifest.json`

Each file stores a `tournaments` object keyed by tournament ID/slug.

Example (`tournament.json`):

```json
{
  "tournaments": {
    "my_tournament": {
      "id": 123,
      "name": "My Tournament",
      "state": "underway"
    }
  }
}
```

Example (`manifest.json`):

```json
{
  "tournaments": {
    "my_tournament": {
      "schema_version": "1.0.0",
      "generated_at": "2026-04-26T18:00:00+00:00",
      "source_tournament_id": "my_tournament",
      "participants_count": 42,
      "matches_count": 84,
      "publish_status": "complete"
    }
  }
}
```

## Terraform

Terraform files are under `infra/terraform/envs/prod`.

### Resources created

- S3 bucket (private) for site + data files
- CloudFront distribution with:
  - optimized cache for static assets
  - low TTL cache policy for `data/*`
- Lambda updater (`mcchallonge-update-data` by default)
- EventBridge scheduled trigger for Lambda
- IAM role/policy for Lambda log and S3 write access

### Bootstrap

```bash
cd infra/terraform/envs/prod
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars values
terraform init
terraform plan
terraform apply
```

### Important terraform variables

- `aws_region`
- `site_bucket_name`
- `tournament_ids`
- `challonge_user`
- `challonge_key`
- `lambda_function_name`
- `schedule_expression`

## Lambda updater

Handler:

- `mcchallonge.lambda_handlers.update_data.lambda_handler`

Code path:

- `mcchallonge/lambda_handlers/update_data.py`

Environment variables expected by Lambda:

- `challonge_user`
- `challonge_key`
- `CHALLONGE_TOURNAMENT_IDS`
- `MCCHALLONGE_DATA_BUCKET`
- `MCCHALLONGE_DATA_PREFIX` (default: `data`)

Publish order is intentional:

1. `tournament.json`
2. `participants.json`
3. `matches.json`
4. `manifest.json` (last, marks refresh complete)

## GitHub Actions

### Infra workflow

- `.github/workflows/infra.yml`
- Runs terraform fmt/validate/plan on pull requests.
- Runs terraform apply on push to `main`.

### Site workflow

- `.github/workflows/deploy-site.yml`
- Builds static site (`python -m mcchallonge.app build`)
- Syncs `build/` to S3 excluding `data/*`
- Invalidates key CloudFront paths

### Lambda workflow

- `.github/workflows/deploy-lambda.yml`
- Packages Lambda zip from project code + dependencies
- Updates Lambda function code
- Invokes Lambda once after deploy

## Required GitHub repository configuration

### Secrets

- `AWS_ROLE_TO_ASSUME`
- `CHALLONGE_USER`
- `CHALLONGE_KEY`

### Variables

- `AWS_REGION`
- `MCCHALLONGE_SITE_BUCKET`
- `MCCHALLONGE_CLOUDFRONT_DISTRIBUTION_ID`
- `MCCHALLONGE_LAMBDA_FUNCTION_NAME`
- `MCCHALLONGE_TOURNAMENT_IDS`

## OIDC IAM setup (recommended)

Use GitHub OIDC for AWS auth instead of static access keys.

- Create an IAM role trusted for your repo's GitHub Actions identity.
- Attach permissions needed for Terraform and deployment actions.
- Store that role ARN in `AWS_ROLE_TO_ASSUME` secret.

## Caching strategy

- Static assets: long-lived CloudFront caching.
- `/data/*`: low TTL policy and `Cache-Control: no-cache, must-revalidate` set by Lambda.
- Optionally run targeted CloudFront invalidation for `/data/*` if freshness requirements are stricter than TTL.

## Local development modes

- API mode (default): uses Flask endpoints (`/api/cache...`).
- Fixed mode: reads `/data/*.json` directly.

Environment flags:

- `MCCHALLONGE_CLIENT_DATA_MODE=api|fixed`
- `MCCHALLONGE_CLIENT_DATA_ROOT=/data`

When running `python -m mcchallonge.app build`, fixed mode is automatically applied for generated static pages.

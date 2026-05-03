provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = "mcchallonge"
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}

# Terraform + provider pinning. The Google provider authenticates via your
# Application Default Credentials (gcloud auth application-default login),
# so no service-account key file is needed anywhere in this repo.

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Run JOB (run-to-completion), not a Service: a migration is a batch
# task that runs and exits, not a request handler. It runs as the dedicated
# service account, so it inherits BigQuery access with no key files. Config is
# injected via env vars; the DB password comes from Secret Manager.

locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}/${var.job_name}:${var.image_tag}"
}

resource "google_cloud_run_v2_job" "migration" {
  name     = var.job_name
  location = var.region
  project  = var.project_id

  deletion_protection = false

  template {
    template {
      service_account = google_service_account.migration_job.email
      timeout         = "600s"
      max_retries     = 1

      containers {
        image = local.image

        env {
          name  = "TARGET_BACKEND"
          value = "bigquery"
        }
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "BQ_DATASET"
          value = var.bq_dataset
        }
        env {
          name  = "BQ_LOCATION"
          value = var.bq_location
        }
        env {
          name  = "TARGET_STATES"
          value = "CA,OR,WA"
        }
        env {
          name  = "LOG_LEVEL"
          value = "INFO"
        }

        # DB password sourced from Secret Manager (used on the Postgres path).
        env {
          name = "POSTGRES_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled,
    google_secret_manager_secret_version.db_password,
    google_project_iam_member.job_roles,
  ]
}

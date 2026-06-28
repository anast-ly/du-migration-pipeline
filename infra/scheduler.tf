# Cloud Scheduler triggers the Cloud Run Job daily. Scheduler has no native
# "run job" action, so it calls the Run Admin API endpoint (:run) over HTTP,
# authenticated with OAuth as a dedicated invoker service account.

# Invoker SA used by Scheduler to execute the job.
resource "google_service_account" "scheduler_invoker" {
  project      = var.project_id
  account_id   = "du-migration-scheduler"
  display_name = "Ducks Unlimited migration scheduler invoker"

  depends_on = [google_project_service.enabled]
}

# Allow that SA to run THIS job (run.invoker scoped to the job).
resource "google_cloud_run_v2_job_iam_member" "scheduler_can_run" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.migration.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}

resource "google_cloud_scheduler_job" "daily_migration" {
  name      = "${var.job_name}-daily"
  project   = var.project_id
  region    = var.region
  schedule  = var.scheduler_cron
  time_zone = "Etc/UTC"

  http_target {
    http_method = "POST"
    uri = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.job_name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_invoker.email
    }
  }

  depends_on = [
    google_project_service.enabled,
    google_cloud_run_v2_job_iam_member.scheduler_can_run,
  ]
}

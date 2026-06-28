# DB password stored in Secret Manager rather than in env files or image.
# The Cloud Run Job reads it as POSTGRES_PASSWORD (wired in cloud_run.tf).
# Used when the job targets Postgres / Cloud SQL; harmless for BigQuery runs.

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "du-postgres-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

# Let the job's service account read this secret.
resource "google_secret_manager_secret_iam_member" "job_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.job_sa_member
}

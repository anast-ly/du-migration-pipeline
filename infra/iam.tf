# Dedicated service account for the migration job, with least-privilege roles.
# The job needs to write to BigQuery and read its secret. Roles are granted at
# project level here for simplicity; they could be scoped to the dataset/secret
# for tighter least-privilege in a real environment.

resource "google_service_account" "migration_job" {
  project      = var.project_id
  account_id   = "du-migration-job"
  display_name = "Ducks Unlimited migration job"

  depends_on = [google_project_service.enabled]
}

locals {
  job_sa_member = "serviceAccount:${google_service_account.migration_job.email}"

  job_roles = [
    "roles/bigquery.dataEditor", # write rows into the dataset
    "roles/bigquery.jobUser",    # run BigQuery load jobs
  ]
}

resource "google_project_iam_member" "job_roles" {
  for_each = toset(local.job_roles)

  project = var.project_id
  role    = each.value
  member  = local.job_sa_member
}

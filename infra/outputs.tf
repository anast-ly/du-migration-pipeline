output "artifact_registry_repo" {
  description = "Full path of the Docker repository."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}"
}

output "migration_image" {
  description = "Image reference the Cloud Run Job deploys."
  value       = local.image
}

output "cloud_run_job" {
  description = "Cloud Run Job name."
  value       = google_cloud_run_v2_job.migration.name
}

output "bigquery_dataset" {
  description = "Target BigQuery dataset."
  value       = google_bigquery_dataset.migration.dataset_id
}

output "scheduler_job" {
  description = "Cloud Scheduler job that triggers the migration."
  value       = google_cloud_scheduler_job.daily_migration.name
}

output "run_job_manually" {
  description = "Command to trigger the job on demand."
  value       = "gcloud run jobs execute ${var.job_name} --region ${var.region}"
}

# --- Values to paste into GitHub repo secrets ---
output "wif_provider" {
  description = "Workload Identity provider resource name (GitHub secret WIF_PROVIDER)."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "deployer_sa" {
  description = "Deployer service account email (GitHub secret DEPLOYER_SA)."
  value       = google_service_account.deployer.email
}

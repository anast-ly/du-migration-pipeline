# All inputs are variables with sensible defaults so a teammate can apply
# against their own project by overriding just project_id (and the image).

variable "project_id" {
  description = "GCP project ID to deploy into."
  type        = string
  default     = "assessment-500800"
}

variable "region" {
  description = "Region for Cloud Run, Artifact Registry, Scheduler."
  type        = string
  default     = "europe-west2"
}

# --- BigQuery (target) ---
variable "bq_location" {
  description = "BigQuery dataset location (multi-region or region)."
  type        = string
  default     = "europe-west2"
}

variable "bq_dataset" {
  description = "BigQuery dataset name."
  type        = string
  default     = "du_migration"
}

# --- Artifact Registry ---
variable "artifact_repo" {
  description = "Artifact Registry repository name for the migration image."
  type        = string
  default     = "du-migration"
}

variable "image_tag" {
  description = "Tag of the migration image to deploy (e.g. latest or a git SHA)."
  type        = string
  default     = "latest"
}

# --- Job / scheduling ---
variable "job_name" {
  description = "Name of the Cloud Run Job."
  type        = string
  default     = "du-migration-job"
}

variable "scheduler_cron" {
  description = "Cron schedule for the daily migration run (UTC)."
  type        = string
  default     = "0 6 * * *" # every day at 06:00 UTC
}

# --- Secrets / optional Cloud SQL ---
variable "db_password" {
  description = "Postgres password stored in Secret Manager (override in tfvars)."
  type        = string
  default     = "changeme"
  sensitive   = true
}

variable "enable_cloud_sql" {
  description = "Provision a Cloud SQL Postgres instance (costs money — off by default)."
  type        = bool
  default     = false
}

variable "github_repo" {
  description = "GitHub repo (owner/name) allowed to authenticate via Workload Identity Federation."
  type        = string
  default     = "anast-ly/du-migration-pipeline"
}

variable "target_states" {
  description = "Comma-separated US state codes to migrate."
  type        = string
  default     = "CA,OR,WA"
}

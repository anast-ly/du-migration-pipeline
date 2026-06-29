# Optional Cloud SQL Postgres target.
# Gated by enable_cloud_sql and OFF by default: Cloud SQL has no free tier, so it
# bills by the hour. Provision it only for a demo and `terraform destroy` after.
#
# This provisions the instance, database and user. Wiring the Cloud Run Job to it
# (via the Cloud SQL connector, with TARGET_BACKEND=postgres) is the documented
# next step — the loader already supports Postgres.

resource "google_sql_database_instance" "postgres" {
  count = var.enable_cloud_sql ? 1 : 0

  project          = var.project_id
  name             = "du-migration-pg"
  region           = var.region
  database_version = "POSTGRES_16"

  # Allow `terraform destroy` to remove it cleanly after a demo.
  deletion_protection = false

  settings {
    tier              = "db-f1-micro" # cheapest shared-core tier; bump for real workloads
    availability_type = "ZONAL"
    disk_size         = 10

    ip_configuration {
      ipv4_enabled = true
    }
  }

  depends_on = [google_project_service.enabled]
}

resource "google_sql_database" "migration" {
  count = var.enable_cloud_sql ? 1 : 0

  project  = var.project_id
  name     = "du_migration"
  instance = google_sql_database_instance.postgres[0].name
}

resource "google_sql_user" "migration" {
  count = var.enable_cloud_sql ? 1 : 0

  project  = var.project_id
  name     = "migration"
  instance = google_sql_database_instance.postgres[0].name
  password = var.db_password # same value stored in Secret Manager
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name (null when disabled)."
  value       = try(google_sql_database_instance.postgres[0].connection_name, null)
}

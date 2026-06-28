# The dataset is infra (owned by Terraform). The TABLE is created by the
# application loader (_ensure_table) so the schema has a single source of
# truth in Python. Both coexist: the loader's create_table(exists_ok=True)
# is a no-op once the dataset exists.

resource "google_bigquery_dataset" "migration" {
  project     = var.project_id
  dataset_id  = var.bq_dataset
  location    = var.bq_location
  description = "Ducks Unlimited university chapters — migration target"

  depends_on = [google_project_service.enabled]
}

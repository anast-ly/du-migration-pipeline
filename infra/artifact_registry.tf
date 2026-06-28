# Docker registry that holds the migration image. CI/CD (and your local
# build) push here; the Cloud Run Job pulls from here.

resource "google_artifact_registry_repository" "migration" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo
  description   = "Ducks Unlimited migration job images"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled]
}

# Keyless auth for GitHub Actions via Workload Identity Federation.
# GitHub presents an OIDC token; GCP verifies it and grants short-lived access
# by letting the repo's identities impersonate a dedicated deployer SA.
# No JSON key exists anywhere; CI authenticates via short-lived federated tokens.

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions pool"

  depends_on = [google_project_service.enabled]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # REQUIRED by GCP for the shared GitHub issuer: restrict to THIS repo only,
  # otherwise any GitHub repo could request tokens (confused-deputy risk).
  attribute_condition = "assertion.repository == \"${var.github_repo}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Deployer SA that GitHub Actions impersonates.
resource "google_service_account" "deployer" {
  project      = var.project_id
  account_id   = "du-migration-deployer"
  display_name = "CI/CD deployer (GitHub Actions)"

  depends_on = [google_project_service.enabled]
}

# Let identities from this repo impersonate the deployer SA.
resource "google_service_account_iam_member" "wif_impersonation" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# Deployer permissions: push images + update the Cloud Run Job.
resource "google_project_iam_member" "deployer_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# To deploy a job that RUNS AS the runtime SA, the deployer must be able to
# act as that SA (scoped to it, not project-wide).
resource "google_service_account_iam_member" "deployer_act_as_runtime" {
  service_account_id = google_service_account.migration_job.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}

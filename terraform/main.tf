terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = file("sa-key.json")
}

# --- Artifact Registry (private container registry) ---

resource "google_artifact_registry_repository" "etl" {
  location      = var.region
  repository_id = "du-chapters-etl"
  format        = "DOCKER"
  description   = "Docker images for DU chapters ETL pipeline"
}

# --- Service Account ---

resource "google_service_account" "etl_runner" {
  account_id   = "du-etl-runner"
  display_name = "DU Chapters ETL Runner"
}

resource "google_project_iam_member" "etl_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.etl_runner.email}"
}

# --- Cloud Run Job ---

resource "google_cloud_run_v2_job" "etl" {
  name     = "du-chapters-etl"
  location = var.region

  template {
    template {
      service_account = google_service_account.etl_runner.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.etl.repository_id}/du-chapters-etl:latest"

        env {
          name  = "DB_HOST"
          value = var.db_host
        }
        env {
          name  = "DB_PORT"
          value = var.db_port
        }
        env {
          name  = "DB_NAME"
          value = var.db_name
        }
        env {
          name  = "DB_USER"
          value = var.db_user
        }
        env {
          name  = "DB_PASSWORD"
          value = var.db_password
        }
        env {
          name  = "STATE_FILTER"
          value = var.state_filter
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }

      max_retries = 1
      timeout     = "300s"
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }
}

# --- Cloud Scheduler (daily trigger) ---

resource "google_cloud_scheduler_job" "etl_daily" {
  name      = "du-chapters-etl-daily"
  region    = var.region
  schedule  = var.schedule
  time_zone = "UTC"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.etl.name}:run"

    oauth_token {
      service_account_email = google_service_account.etl_runner.email
    }
  }
}

# Grant the service account permission to invoke the Cloud Run job
resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  name     = google_cloud_run_v2_job.etl.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.etl_runner.email}"
}

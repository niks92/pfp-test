output "artifact_registry_url" {
  description = "Docker image push URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.etl.repository_id}"
}

output "cloud_run_job_name" {
  description = "Name of the Cloud Run job"
  value       = google_cloud_run_v2_job.etl.name
}

output "scheduler_job_name" {
  description = "Name of the Cloud Scheduler trigger"
  value       = google_cloud_scheduler_job.etl_daily.name
}

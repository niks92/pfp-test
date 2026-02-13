variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "europe-west2"
}

variable "db_host" {
  description = "Postgres host (cloud-hosted instance)"
  type        = string
}

variable "db_port" {
  description = "Postgres port"
  type        = string
  default     = "5432"
}

variable "db_name" {
  description = "Postgres database name"
  type        = string
  default     = "du_chapters"
}

variable "db_user" {
  description = "Postgres user"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Postgres password"
  type        = string
  sensitive   = true
}

variable "state_filter" {
  description = "US state abbreviation to filter chapters"
  type        = string
  default     = "CA"
}

variable "schedule" {
  description = "Cron schedule for the Cloud Run job (daily at 06:00 UTC)"
  type        = string
  default     = "0 6 * * *"
}

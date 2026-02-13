# DU University Chapters ETL Pipeline

An ETL pipeline that extracts Ducks Unlimited university chapter data from the [ArcGIS Feature Service](https://gis.ducks.org/datasets/du-university-chapters/api), transforms it, and loads it into a Postgres database.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  DU ArcGIS   │────▶│   Extract    │────▶│  Transform   │────▶│   Load   │
│  Feature API │     │ (requests)   │     │ (dataclass)  │     │ (psycopg2│
└──────────────┘     └──────────────┘     └──────────────┘     │  upsert) │
                                                                └────┬─────┘
                                                                     │
                                                                ┌────▼─────┐
                                                                │ Postgres │
                                                                └──────────┘
```

**Pipeline stages:**

| Stage | Module | Responsibility |
|-------|--------|----------------|
| Extract | `src/extract.py` | Queries the ArcGIS REST API filtered by state |
| Transform | `src/transform.py` | Normalises raw features into `Chapter` dataclasses, skips invalid records |
| Load | `src/load.py` | Upserts records into `university_chapters` table (idempotent) |
| Orchestrator | `src/pipeline.py` | Wires the stages together with logging and error handling |
| Config | `src/config.py` | Loads settings from environment variables |

**Cloud deployment (GCP):**

| Component | Purpose |
|-----------|---------|
| Cloud Run Job | Runs the containerised ETL |
| Cloud Scheduler | Triggers the job daily at 06:00 UTC |
| Artifact Registry | Private Docker image registry |
| Terraform | Provisions all infrastructure |
| GitHub Actions | CI (lint + test) and CD (build, push, deploy) |

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- `gcloud` CLI (authenticated)
- Terraform >= 1.5

## Local Environment Setup

### Step 1 — Clone and set up Python

```bash
# Clone the repo
git clone <repo-url> && cd pfp

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dev dependencies (includes test + lint tools)
pip install -r requirements-dev.txt
```

### Step 2 — Run the ETL locally with Docker Compose

Docker Compose starts a local Postgres container and runs the ETL against it — no cloud resources needed.

```bash
# Start Postgres + run ETL (builds the image from Dockerfile)
docker compose up --build

# Verify data was loaded
docker compose exec db psql -U postgres -d du_chapters \
  -c "SELECT chapter_id, chapter_name, city, state, longitude, latitude FROM university_chapters;"
```

Expected output:

```
 chapter_id |              chapter_name               |      city       | state |      longitude      |      latitude
------------+-----------------------------------------+-----------------+-------+---------------------+--------------------
 CA-0355    | California Polytechnic State University  | San Luis Obispo | CA    | -120.66319100299995 | 35.274309145000075
 CA-0300    | Chico State University                   | Chico           | CA    | -121.83546324499997 |  39.73998176200007
 CA-0362    | Fresno State                             | Fresno          | CA    | -119.73959481924653 |  36.82354541564933
```

The ETL runs once and exits. The Postgres data persists in a Docker volume. To reset:

```bash
docker compose down -v   # removes volumes
```

### Step 3 — Run tests and linting

```bash
source .venv/bin/activate

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint
ruff check src/ tests/
```

### Step 4 — GCP project setup and Terraform

#### 4a. Enable required GCP APIs

```bash
export GCP_PROJECT=<your-gcp-project-id>

gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project=$GCP_PROJECT
```

#### 4b. Create a Terraform service account

Terraform needs a dedicated service account to provision resources. Your `gcloud` user must have **Owner** role on the project to perform this step.

```bash
# Create the service account
gcloud iam service-accounts create terraform-deployer \
  --display-name="Terraform Deployer" \
  --project=$GCP_PROJECT

# Grant required roles
gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:terraform-deployer@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/editor" --quiet

gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:terraform-deployer@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountAdmin" --quiet

gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:terraform-deployer@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin" --quiet

gcloud projects add-iam-policy-binding $GCP_PROJECT \
  --member="serviceAccount:terraform-deployer@$GCP_PROJECT.iam.gserviceaccount.com" \
  --role="roles/run.admin" --quiet

# Download the key (used by Terraform provider)
gcloud iam service-accounts keys create terraform/sa-key.json \
  --iam-account=terraform-deployer@$GCP_PROJECT.iam.gserviceaccount.com
```

> **Note:** `terraform/sa-key.json` is in `.gitignore` — never commit service account keys.

**IAM roles summary for the Terraform service account:**

| Role | Why |
|------|-----|
| `roles/editor` | Create Artifact Registry, Cloud Run Jobs, Cloud Scheduler |
| `roles/iam.serviceAccountAdmin` | Create the ETL runner service account |
| `roles/resourcemanager.projectIamAdmin` | Bind IAM roles (log writer, invoker) |
| `roles/run.admin` | Set IAM policies on Cloud Run jobs |

#### 4c. Build and push the Docker image

The Cloud Run Job needs an image to exist in Artifact Registry before Terraform can create the job.

```bash
# Authenticate Docker to push to Artifact Registry
gcloud auth configure-docker europe-west2-docker.pkg.dev --quiet

# Build and push
docker build -t europe-west2-docker.pkg.dev/$GCP_PROJECT/du-chapters-etl/du-chapters-etl:latest .
docker push europe-west2-docker.pkg.dev/$GCP_PROJECT/du-chapters-etl/du-chapters-etl:latest
```

#### 4d. Run Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project ID and DB credentials

terraform init
terraform plan    # Review what will be created
terraform apply   # Provision infrastructure
```

This provisions:
- **Artifact Registry** — private Docker image repository
- **Cloud Run Job** — runs the ETL container
- **Cloud Scheduler** — triggers the job daily at 06:00 UTC
- **Service Account** (`du-etl-runner`) — least-privilege identity for the job
- **IAM bindings** — log writer + scheduler invoker permissions

#### Note on Postgres in the cloud

Terraform does **not** provision a Cloud SQL instance. The task states: *"You can work under the assumption that the service is accessing a cloud hosted Postgres instance, or deploy the cloud hosted instance."*

We chose Option A — **assume an external Postgres exists**. The Cloud Run Job receives the DB connection details (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, etc.) as environment variables via Terraform. This keeps costs down (Cloud SQL starts at ~$30/month) and keeps the ETL service stateless and DB-agnostic.

For local testing, Docker Compose provides a Postgres container. When a cloud Postgres instance is available, simply update the `db_*` values in `terraform.tfvars` and re-apply — the ETL code does not change.

> `terraform.tfvars` contains credentials and is in `.gitignore`. Only `terraform.tfvars.example` is committed.

#### Note on Terraform state

Terraform state is stored **locally** (`terraform/terraform.tfstate`, gitignored). For a single-developer assessment this is sufficient. In a team/production environment, state should be stored in a **GCS backend** with locking to prevent concurrent modifications:

```hcl
terraform {
  backend "gcs" {
    bucket = "my-tf-state-bucket"
    prefix = "du-chapters-etl"
  }
}
```

This was intentionally omitted to keep the setup simple and avoid provisioning additional resources.

## Configuration

All config is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Postgres host |
| `DB_PORT` | `5432` | Postgres port |
| `DB_NAME` | `du_chapters` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `STATE_FILTER` | `CA` | US state code to filter chapters |

## Cloud Deployment (GCP)

### Deployment strategy — separation of concerns

Infrastructure provisioning (Terraform) and application deployment (GitHub Actions) are intentionally kept separate:

| Concern | Tool | Trigger |
|---------|------|---------|
| **Infrastructure** (Artifact Registry, Cloud Run Job, Scheduler, IAM) | Terraform | Run locally or via a dedicated infra pipeline when resources change |
| **Application** (build image, push, update Cloud Run image tag) | GitHub Actions | Automatically on every push to `main` |

**Trade-Off** 

Ideally, in a production environment we would have **separate GCP projects** for each stage (e.g. `dev`, `staging`, `prod`). Infrastructure changes would be tested locally against the dev project, reviewed via PR, promoted to staging, and only then applied to production. The CI/CD pipeline would handle application deployments across all environments independently.

However, for this assessment a **single GCP project** is used to minimise infrastructure costs. Terraform is applied locally to provision the resources once, and GitHub Actions handles all subsequent application changes — building, testing, and deploying the updated image to the same project.

### 1. Set up Terraform (one-time, local)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your GCP project and DB credentials

terraform init
terraform plan    # Review what will be created
terraform apply   # Provision infrastructure
```

This provisions:
- Artifact Registry repository (private Docker registry)
- Cloud Run Job (configured to connect to your Postgres host)
- Cloud Scheduler job (daily at 06:00 UTC)
- Service account with least-privilege IAM roles

### 2. CI/CD (GitHub Actions — automated on every push)

The deploy pipeline uses **Workload Identity Federation** (keyless auth). Set these GitHub secrets:

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `WIF_PROVIDER` | Workload Identity Provider resource name |
| `WIF_SERVICE_ACCOUNT` | Service account email for GitHub Actions |

On push to `main`:
1. **CI** — lint + test
2. **Deploy** — build image, push to Artifact Registry, update Cloud Run job

## File Structure

```
pfp/
├── src/
│   ├── __init__.py
│   ├── config.py          # Environment-based configuration
│   ├── extract.py         # API data extraction
│   ├── transform.py       # Data transformation & validation
│   ├── load.py            # Postgres upsert logic
│   └── pipeline.py        # ETL orchestrator & entrypoint
├── tests/
│   ├── test_extract.py    # API extraction tests (mocked HTTP)
│   ├── test_transform.py  # Transformation logic tests
│   └── test_load.py       # Database load tests (mocked DB)
├── terraform/
│   ├── main.tf            # GCP resources (Cloud Run, Scheduler, IAM)
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # Useful output values
│   └── terraform.tfvars.example
├── db/
│   └── init.sql           # Postgres table schema (used by Docker)
├── .github/workflows/
│   ├── ci.yml             # Lint & test on PR/push
│   └── deploy.yml         # Build, push, deploy on main
├── Dockerfile
├── docker-compose.yml     # Local testing stack
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

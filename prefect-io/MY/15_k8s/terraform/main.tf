##################################################
# Prefect Flow Resource
##################################################
# Register the flow in Prefect

resource "prefect_flow" "my_first_workflow" {
  name = "my-first-workflow"
  tags = ["kubernetes", "etl", "terraform"]
}

##################################################
# Prefect Deployment for Kubernetes
##################################################

resource "prefect_deployment" "my_first_workflow_deployment" {
  name = var.deployment_name

  # Required: Flow ID to deploy
  flow_id = prefect_flow.my_first_workflow.id

  # Work pool configuration
  work_pool_name = var.work_pool_name

  # Flow entrypoint
  entrypoint = var.flow_entrypoint

  # Path where the flow code is located in the Docker image
  path = "/app"

  # Job variables for Kubernetes work pool
  job_variables = jsonencode({
    # Kubernetes-specific configuration
    image = var.docker_image
    image_pull_policy = "Always"

    # Resource limits (adjust as needed)
    limits = {
      cpu    = "1000m"
      memory = "512Mi"
    }

    requests = {
      cpu    = "100m"
      memory = "128Mi"
    }

    # Environment variables passed to the pod
    env = {
      PREFECT_API_URL = var.prefect_api_url
    }

    # Optional: Add labels to the Kubernetes job
    labels = {
      app = "prefect-flow"
      deployment = var.deployment_name
    }

    # Optional: If you need to pull from private Docker registry
    # image_pull_secrets = ["dockerhub-secret"]
  })

  # Optional: Schedule (uncomment if you want scheduled runs)
  # Note: Schedules are now managed as a separate resource in Terraform
  # See prefect_deployment_schedule resource below

  # Flow parameters (default values)
  parameters = jsonencode({
    source      = "database"
    destination = "warehouse"
  })

  # Description
  description = "ETL workflow deployed to Kubernetes via Terraform"

  # Tags for organization
  tags = ["kubernetes", "etl", "terraform"]
}

##################################################
# Optional: Deployment Schedule
##################################################
# Uncomment this resource if you want to add a schedule to the deployment

# resource "prefect_deployment_schedule" "k8s_etl_schedule" {
#   deployment_id = prefect_deployment.k8s_etl_deployment.id
#   active        = true
#
#   # Cron schedule configuration
#   cron     = var.schedule_cron
#   timezone = "UTC"
# }

##################################################
# Outputs
##################################################

output "deployment_id" {
  description = "ID of the created deployment"
  value       = prefect_deployment.my_first_workflow_deployment.id
}

output "deployment_name" {
  description = "Name of the created deployment"
  value       = prefect_deployment.my_first_workflow_deployment.name
}

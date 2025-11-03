variable "prefect_api_url" {
  description = "Prefect API URL (e.g., http://192.168.5.65:4200/api)"
  type        = string
}

variable "docker_image" {
  description = "Docker image for the flow (e.g., yourusername/prefect-k8s-flow:latest)"
  type        = string
}

variable "work_pool_name" {
  description = "Name of the Kubernetes work pool"
  type        = string
  default     = "MyFirstWorkPool"
}

variable "deployment_name" {
  description = "Name of the deployment"
  type        = string
  default     = "k8s-etl-deployment"
}

variable "flow_entrypoint" {
  description = "Entrypoint for the flow (module:function)"
  type        = string
  default     = "flow:k8s_etl_flow"
}

variable "schedule_cron" {
  description = "Cron schedule for the deployment (optional, null for no schedule)"
  type        = string
  default     = null
}

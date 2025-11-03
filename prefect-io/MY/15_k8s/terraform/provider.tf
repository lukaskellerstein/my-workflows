terraform {
  required_providers {
    prefect = {
      source = "PrefectHQ/prefect"
      version = "2.89.0"
    }
  }
}

provider "prefect" {
  # For self-hosted Prefect server, use 'endpoint' instead of 'api_url'
  endpoint = var.prefect_api_url

  # If your Prefect server requires authentication, add:
  # api_key = var.prefect_api_key
  # For self-hosted without auth, this can be omitted
}

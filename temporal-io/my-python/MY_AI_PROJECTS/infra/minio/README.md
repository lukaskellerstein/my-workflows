# Run

```bash
docker compose -p my-minio-with-mcp up -d
```

## MCP Server

https://github.com/minio/mcp-server-aistor

```json
{
  "mcpServers": {
    "aistor": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/home/lukas/Temp/Minio:/Downloads",
        "-e",
        "MINIO_ENDPOINT=http://localhost:9000",
        "-e",
        "MINIO_ACCESS_KEY=admin",
        "-e",
        "MINIO_SECRET_KEY=password123",
        "-e",
        "MINIO_USE_SSL=false",
        "quay.io/minio/aistor/mcp-server-aistor:latest",
        "--allowed-directories",
        "/Downloads",
        "--allow-write",
        "--allow-delete",
        "--allow-admin"
      ]
    }
  }
}
```

# MinIO Object Storage Integration Complete! 🗄️

## Summary

The `generate_audio_report` activity now stores generated audio files in **MinIO object storage** using the aistor MCP server, providing persistent, S3-compatible storage for research audio reports.

## What Changed

### File: `2_agents/activities/agent_activities.py`

**Lines 737-878**: Added MinIO MCP integration for storing audio files:

```python
# Get MinIO configuration
minio_endpoint = os.getenv("MINIO_ENDPOINT")
minio_access_key = os.getenv("MINIO_ACCESS_KEY")
minio_secret_key = os.getenv("MINIO_SECRET_KEY")
minio_use_ssl = os.getenv("MINIO_USE_SSL", "false")
minio_downloads_path = os.getenv("MINIO_DOWNLOADS_PATH", "/tmp/minio")

# After audio generation...
if audio_file_path and minio_endpoint and minio_access_key:
    activity.logger.info("Storing audio file in MinIO")

    try:
        async with MCPServerStdio(
            name="MinIO Storage",
            params={
                "command": "docker",
                "args": [
                    "run",
                    "-i",
                    "--rm",
                    "-v",
                    f"{minio_downloads_path}:/Downloads",
                    "-e",
                    f"MINIO_ENDPOINT={minio_endpoint}",
                    "-e",
                    f"MINIO_ACCESS_KEY={minio_access_key}",
                    "-e",
                    f"MINIO_SECRET_KEY={minio_secret_key}",
                    "-e",
                    f"MINIO_USE_SSL={minio_use_ssl}",
                    "quay.io/minio/aistor/mcp-server-aistor:latest",
                    "--allowed-directories",
                    "/Downloads",
                    "--allow-write",
                    "--allow-delete",
                    "--allow-admin",
                ],
            },
            client_session_timeout_seconds=60.0,
        ) as minio_server:
            agent = Agent(
                name="MinIO Storage Agent",
                model="gpt-5-mini",
                mcp_servers=[minio_server],
                model_settings=ModelSettings(tool_choice="auto"),
                instructions=f"Upload audio file to MinIO bucket 'research-audio'",
            )

            prompt = f"Upload audio file {audio_file_path} to MinIO as {session_id}.mp3"

            result = await Runner.run(starting_agent=agent, input=prompt)
            activity.logger.info("Audio file stored in MinIO")

            # Update URL to MinIO location
            minio_url = f"{minio_endpoint}/research-audio/{session_id}.mp3"

    except Exception as e:
        activity.logger.warning(f"Failed to store in MinIO: {e}")
```

## Environment Configuration

### `.env` File

New MinIO-specific environment variables:

```bash
# MinIO Configuration
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
MINIO_USE_SSL=false
MINIO_DOWNLOADS_PATH=/home/lukas/Temp/Minio
```

### `.env.example` File

Updated with MinIO configuration template:

```bash
# MinIO Configuration
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
MINIO_USE_SSL=false
MINIO_DOWNLOADS_PATH=/home/lukas/Temp/Minio
```

## How It Works

### 1. Audio Generation (ElevenLabs)

First, the activity generates audio using ElevenLabs MCP:

```python
# Generate audio using ElevenLabs
async with MCPServerStdio(name="ElevenLabs TTS", ...) as elevenlabs_server:
    agent = Agent(mcp_servers=[elevenlabs_server], ...)
    result = await Runner.run(starting_agent=agent, input=prompt)

    # Audio saved to local file
    audio_file_path = f"/tmp/audio_{session_id}.mp3"
```

### 2. MinIO Storage

Then, the audio file is uploaded to MinIO:

```python
# Upload to MinIO using aistor MCP
async with MCPServerStdio(name="MinIO Storage", ...) as minio_server:
    agent = Agent(mcp_servers=[minio_server], ...)

    prompt = f"Upload audio file {audio_file_path} to MinIO as {session_id}.mp3"
    result = await Runner.run(starting_agent=agent, input=prompt)
```

### 3. Docker-based MCP Server

MinIO MCP runs as a Docker container:

```bash
docker run -i --rm \
  -v /home/lukas/Temp/Minio:/Downloads \
  -e MINIO_ENDPOINT=http://localhost:9000 \
  -e MINIO_ACCESS_KEY=admin \
  -e MINIO_SECRET_KEY=password123 \
  -e MINIO_USE_SSL=false \
  quay.io/minio/aistor/mcp-server-aistor:latest \
  --allowed-directories /Downloads \
  --allow-write \
  --allow-delete \
  --allow-admin
```

**Key Parameters**:

- **Volume mount**: Maps local directory to `/Downloads` in container
- **Environment variables**: MinIO connection credentials
- **Permissions**: Write, delete, and admin access enabled

### 4. Graceful Fallback

If MinIO storage fails:

```python
except Exception as e:
    activity.logger.warning(f"Failed to store in MinIO: {e}. Using fallback URL.")
    # Audio metadata returned with fallback URL
```

## MinIO Setup

### Prerequisites

1. **MinIO Server Running**:

```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=password123 \
  quay.io/minio/minio server /data --console-address ":9001"
```

2. **Create Bucket**:

```bash
# Using mc (MinIO Client)
mc alias set local http://localhost:9000 admin password123
mc mb local/research-audio
```

Or via MinIO Console:

- Open http://localhost:9001
- Login with admin/password123
- Create bucket named `research-audio`

3. **Downloads Directory**:

```bash
mkdir -p /home/lukas/Temp/Minio
chmod 777 /home/lukas/Temp/Minio
```

## Benefits

### Object Storage

✅ **S3-Compatible**: Standard S3 API for object storage
✅ **Persistent Storage**: Audio files survive workflow restarts
✅ **Scalable**: Handle thousands of audio files
✅ **Accessible**: Direct HTTP access to stored files

### Production Ready

✅ **Docker-based**: Isolated, reproducible environment
✅ **Configurable**: Environment-based configuration
✅ **Graceful Fallback**: Works without MinIO (returns fallback URL)
✅ **Secure**: Access keys and SSL support

## Testing

### Run the Workflow

```bash
# Terminal 1: Start MinIO
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=password123 \
  quay.io/minio/minio server /data --console-address ":9001"

# Terminal 2: Create bucket
mc alias set local http://localhost:9000 admin password123
mc mb local/research-audio

# Terminal 3: Start worker
cd 2_agents
source ../.venv/bin/activate
python run_worker.py

# Terminal 4: Run workflow with audio generation
python run_workflow.py
```

### Expected Log Output (Success)

```
[2025-11-01 16:00:45] INFO: Generating audio report for: Latest AI Research
[2025-11-01 16:00:45] INFO: Using ElevenLabs MCP for audio generation
[2025-11-01 16:00:52] INFO: Audio generated using ElevenLabs MCP
[2025-11-01 16:00:52] INFO: Storing audio file in MinIO
[2025-11-01 16:00:55] INFO: Audio file stored in MinIO  ← MinIO storage!
[2025-11-01 16:00:55] INFO: Audio report generated: 180.0s with 6 chapters
[2025-11-01 16:00:55] INFO: Audio URL: http://localhost:9000/research-audio/audio_research_123.mp3
```

### Verify Storage

```bash
# List files in bucket
mc ls local/research-audio/

# Download file
mc cp local/research-audio/audio_research_123.mp3 ./downloaded.mp3

# Play audio
mpv downloaded.mp3
```

Or via MinIO Console:

- Open http://localhost:9001
- Navigate to `research-audio` bucket
- See uploaded audio files

## Architecture Flow

### Complete Audio Pipeline

```
┌────────────────────────────────────────────────────────┐
│  generate_audio_report Activity                        │
│                                                         │
│  1. Build script from synthesis                        │
│     ↓                                                   │
│  2. ElevenLabs MCP (uvx elevenlabs-mcp)                │
│     - Convert text to speech                           │
│     - Save to /tmp/audio_{session_id}.mp3              │
│     ↓                                                   │
│  3. MinIO MCP (docker mcp-server-aistor)               │
│     - Upload file to MinIO                             │
│     - Store in bucket: research-audio                  │
│     - Filename: {session_id}.mp3                       │
│     ↓                                                   │
│  4. Return AudioReport with MinIO URL                  │
│     - audio_url: http://localhost:9000/research-audio/ │
│     - Accessible via HTTP                              │
└────────────────────────────────────────────────────────┘
```

### Data Flow

```
Research Synthesis
    ↓
Script Generation (text)
    ↓
ElevenLabs API (via MCP)
    ↓
Audio File (/tmp/audio_{id}.mp3)
    ↓
MinIO Storage (via MCP + Docker)
    ↓
S3-Compatible Object Storage
    ↓
HTTP URL (http://localhost:9000/research-audio/{id}.mp3)
```

## File Organization

### Local Temporary Storage

```
/tmp/
  └── audio_research_20251101-160045.mp3  ← ElevenLabs output
```

### MinIO Storage Path

```
/home/lukas/Temp/Minio/  ← Local downloads folder (mounted to Docker)
  └── Mapped to /Downloads in Docker container
```

### MinIO Bucket Structure

```
research-audio/
  ├── audio_research_20251101-160045.mp3
  ├── audio_research_20251101-160123.mp3
  └── audio_research_20251101-160245.mp3
```

## Access Audio Files

### Direct HTTP Access

```bash
# Download via curl
curl -O http://localhost:9000/research-audio/audio_research_123.mp3

# Stream via wget
wget http://localhost:9000/research-audio/audio_research_123.mp3

# Play directly (if mpv supports HTTP)
mpv http://localhost:9000/research-audio/audio_research_123.mp3
```

### Via MinIO Client (mc)

```bash
# List all audio files
mc ls local/research-audio/

# Download specific file
mc cp local/research-audio/audio_research_123.mp3 ./

# Get file info
mc stat local/research-audio/audio_research_123.mp3

# Delete old files
mc rm local/research-audio/audio_old.mp3
```

### Via MinIO Console (Web UI)

1. Open http://localhost:9001
2. Login with admin/password123
3. Navigate to `research-audio` bucket
4. Browse, download, or delete files

## MCP Integration Patterns

Project 2 now demonstrates **four different MCP integrations**:

1. **Tavily (HTTP)**: `MCPServerStreamableHttp` for web search
2. **arXiv (subprocess)**: `MCPServerStdio` for academic papers
3. **ElevenLabs (subprocess)**: `MCPServerStdio` for text-to-speech
4. **MinIO (Docker)**: `MCPServerStdio` with Docker for object storage

Each demonstrates a different integration pattern:

- HTTP-based MCP servers
- Subprocess-based MCP servers
- Docker-based MCP servers with volume mounts

## Security Considerations

### Production Recommendations

1. **Use SSL/TLS**:

```bash
MINIO_USE_SSL=true
MINIO_ENDPOINT=https://minio.yourcompany.com
```

2. **Strong Credentials**:

```bash
MINIO_ACCESS_KEY=<strong-access-key>
MINIO_SECRET_KEY=<strong-secret-key>
```

3. **Bucket Policies**: Restrict access to specific users/applications

4. **Network Isolation**: Run MinIO in private network

## Troubleshooting

### MinIO Not Accessible

**Error**: "Failed to store in MinIO: Connection refused"

**Solution**:

```bash
# Check if MinIO is running
docker ps | grep minio

# Start MinIO if not running
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=password123 \
  quay.io/minio/minio server /data --console-address ":9001"
```

### Bucket Doesn't Exist

**Error**: "Bucket 'research-audio' not found"

**Solution**:

```bash
mc alias set local http://localhost:9000 admin password123
mc mb local/research-audio
```

### Permission Denied

**Error**: "Access denied"

**Solution**: Check MinIO credentials match .env configuration

## Summary

🗄️ **MinIO MCP is now integrated!**

The Research Assistant workflow now:

1. ✅ Generates audio using **ElevenLabs MCP**
2. ✅ Stores audio files in **MinIO object storage**
3. ✅ Returns **accessible HTTP URLs** for audio playback
4. ✅ Provides **S3-compatible** persistent storage

This completes the fourth MCP integration, providing production-ready object storage for generated audio files! 🚀

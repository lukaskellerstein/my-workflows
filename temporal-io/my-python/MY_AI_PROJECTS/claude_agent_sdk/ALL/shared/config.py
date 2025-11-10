"""Configuration management for all projects.

This module handles configuration for:
- Temporal.io (workflow orchestration)
- MongoDB (data persistence)
- Application settings (logging, retries, timeouts)

Note: MCP server configurations are in mcp_config.py
Note: Claude SDK configurations are in sdk_wrapper.py
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class TemporalConfig:
    """Temporal server configuration."""

    host: str = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace: str = os.getenv("TEMPORAL_NAMESPACE", "default")


@dataclass
class MongoDBConfig:
    """MongoDB configuration."""

    connection_string: str = os.getenv(
        "MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/temporal_claude_sdk"
    )
    database_name: str = "temporal_claude_sdk"


@dataclass
class AppConfig:
    """Application-wide configuration."""

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "300"))

    temporal: TemporalConfig = field(default_factory=TemporalConfig)
    mongodb: MongoDBConfig = field(default_factory=MongoDBConfig)


# Global config instance
config = AppConfig()

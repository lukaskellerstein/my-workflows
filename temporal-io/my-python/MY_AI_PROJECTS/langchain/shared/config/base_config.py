"""Base configuration classes for the projects."""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class TemporalConfig(BaseModel):
    """Configuration for Temporal connection."""

    host: str = Field(default="localhost:7233", description="Temporal server host")
    namespace: str = Field(default="default", description="Temporal namespace")
    task_queue_prefix: str = Field(
        default="langchain-temporal", description="Prefix for task queue names"
    )


class LangchainConfig(BaseModel):
    """Configuration for Langchain models."""

    anthropic_api_key: str = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""),
        description="Anthropic API key",
    )
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key",
    )
    default_model: str = Field(
        default="claude-sonnet-4-20250514", description="Default LLM model to use"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="LLM temperature"
    )
    max_tokens: int = Field(
        default=4096, ge=1, description="Maximum tokens for LLM responses"
    )


class MongoDBConfig(BaseModel):
    """Configuration for MongoDB connection."""

    connection_string: str = Field(
        default_factory=lambda: os.getenv(
            "MONGODB_URI", "mongodb://localhost:27017/"
        ),
        description="MongoDB connection string",
    )
    database_name: str = Field(
        default="langchain_temporal", description="Database name"
    )


class BaseConfig(BaseModel):
    """Base configuration combining all configs."""

    temporal: TemporalConfig = Field(default_factory=TemporalConfig)
    langchain: LangchainConfig = Field(default_factory=LangchainConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)

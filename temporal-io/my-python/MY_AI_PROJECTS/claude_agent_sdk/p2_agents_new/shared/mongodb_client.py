"""MongoDB client for persistent storage.

Note: Uses PyMongo's native async API (Motor is deprecated as of May 14, 2025)
"""

import logging
from typing import Any, Dict, List, Optional

from pymongo import AsyncMongoClient, IndexModel
from pymongo.errors import DuplicateKeyError

from .config import config

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Async MongoDB client for research data storage using PyMongo async API."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or config.mongodb.connection_string
        self.client: Optional[AsyncMongoClient] = None
        self.db = None

    async def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            self.client = AsyncMongoClient(self.connection_string)

            # Extract database name from connection string if present
            # Format: mongodb://host:port/database_name
            if "/" in self.connection_string.split("://")[1]:
                db_name = self.connection_string.split("/")[-1].split("?")[0]
                if db_name:
                    self.db = self.client[db_name]
                else:
                    self.db = self.client[config.mongodb.database_name]
            else:
                self.db = self.client[config.mongodb.database_name]

            # Verify connection
            await self.client.admin.command("ping")
            logger.info(f"Successfully connected to MongoDB using PyMongo async API (database: {self.db.name})")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_indexes(self) -> None:
        """Create indexes for optimal query performance."""
        if self.db is None:
            raise RuntimeError("Database not connected")

        # Indexes for research_sources collection
        sources_indexes = [
            IndexModel([("type", 1)]),
            IndexModel([("topics", 1)]),
            IndexModel([("date_collected", -1)]),
            IndexModel([("credibility_score", -1)]),
            IndexModel([("query_id", 1)]),
        ]
        await self.db.research_sources.create_indexes(sources_indexes)

        # Indexes for knowledge_graph collection
        graph_indexes = [
            IndexModel([("type", 1)]),
            IndexModel([("name", 1)]),
            IndexModel([("relationships.target_id", 1)]),
        ]
        await self.db.knowledge_graph.create_indexes(graph_indexes)

        # Indexes for research_sessions collection
        session_indexes = [
            IndexModel([("timestamp", -1)]),
            IndexModel([("query", "text")]),
        ]
        await self.db.research_sessions.create_indexes(session_indexes)

        logger.info("Created database indexes")

    async def insert_document(
        self, collection: str, document: Dict[str, Any]
    ) -> str:
        """Insert a document and return its ID."""
        if self.db is None:
            raise RuntimeError("Database not connected")

        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)

    async def find_documents(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find documents matching a query."""
        if self.db is None:
            raise RuntimeError("Database not connected")

        cursor = self.db[collection].find(query, projection)

        if limit:
            cursor = cursor.limit(limit)

        documents = await cursor.to_list(length=None)
        return documents

    async def update_document(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
        """Update documents matching a query."""
        if self.db is None:
            raise RuntimeError("Database not connected")

        result = await self.db[collection].update_many(query, update, upsert=upsert)
        return result.modified_count

    async def aggregate(
        self, collection: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run an aggregation pipeline."""
        if self.db is None:
            raise RuntimeError("Database not connected")

        cursor = self.db[collection].aggregate(pipeline)
        results = await cursor.to_list(length=None)
        return results

    async def count_documents(
        self, collection: str, query: Dict[str, Any]
    ) -> int:
        """Count documents matching a query."""
        if self.db is None:
            raise RuntimeError("Database not connected")

        count = await self.db[collection].count_documents(query)
        return count

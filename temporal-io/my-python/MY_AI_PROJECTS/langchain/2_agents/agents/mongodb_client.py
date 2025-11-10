"""MongoDB client wrapper for research data management."""

from typing import Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResearchMongoClient:
    """MongoDB client for managing research data."""

    def __init__(self, connection_string: str, database_name: str):
        """
        Initialize MongoDB client.

        Args:
            connection_string: MongoDB connection URI
            database_name: Name of the database
        """
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]

        # Collections
        self.sources: Collection = self.db["research_sources"]
        self.knowledge_graph: Collection = self.db["knowledge_graph"]
        self.sessions: Collection = self.db["research_sessions"]

        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create necessary indexes for performance."""
        # Sources collection indexes
        self.sources.create_index([("query_id", ASCENDING)])
        self.sources.create_index([("type", ASCENDING)])
        self.sources.create_index([("topics", ASCENDING)])
        self.sources.create_index([("credibility_score", DESCENDING)])
        self.sources.create_index([("date_collected", DESCENDING)])

        # Knowledge graph indexes
        self.knowledge_graph.create_index([("type", ASCENDING)])
        self.knowledge_graph.create_index([("name", ASCENDING)])

        # Sessions collection indexes
        self.sessions.create_index([("timestamp", DESCENDING)])

        logger.info("MongoDB indexes created successfully")

    def create_session(self, query: str, session_id: str) -> str:
        """
        Create a new research session.

        Args:
            query: Research query
            session_id: Unique session identifier

        Returns:
            Session ID
        """
        session_doc = {
            "_id": session_id,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "sources_collected": 0,
            "total_tokens_used": 0,
            "duration_seconds": 0,
            "status": "in_progress",
        }

        self.sessions.insert_one(session_doc)
        logger.info(f"Created research session: {session_id}")
        return session_id

    def add_source(self, source_data: dict[str, Any]) -> str:
        """
        Add a research source to the database.

        Args:
            source_data: Source metadata and content

        Returns:
            Source ID
        """
        result = self.sources.insert_one(source_data)
        logger.info(f"Added source: {source_data.get('title', 'Unknown')}")
        return str(result.inserted_id)

    def get_sources_by_query(self, query_id: str) -> list[dict]:
        """
        Get all sources for a research query.

        Args:
            query_id: Research session ID

        Returns:
            List of source documents
        """
        return list(self.sources.find({"query_id": query_id}))

    def get_sources_by_topic(
        self, topic: str, limit: int = 10
    ) -> list[dict]:
        """
        Get sources related to a specific topic.

        Args:
            topic: Topic to search for
            limit: Maximum number of results

        Returns:
            List of source documents
        """
        return list(
            self.sources.find({"topics": topic})
            .sort("credibility_score", DESCENDING)
            .limit(limit)
        )

    def add_knowledge_node(self, node_data: dict[str, Any]) -> str:
        """
        Add a node to the knowledge graph.

        Args:
            node_data: Node data including type, name, relationships

        Returns:
            Node ID
        """
        result = self.knowledge_graph.insert_one(node_data)
        logger.info(f"Added knowledge node: {node_data.get('name', 'Unknown')}")
        return str(result.inserted_id)

    def get_related_nodes(
        self, node_id: str, relationship_type: Optional[str] = None
    ) -> list[dict]:
        """
        Get nodes related to a specific node.

        Args:
            node_id: Source node ID
            relationship_type: Optional filter by relationship type

        Returns:
            List of related nodes
        """
        # Find the source node
        node = self.knowledge_graph.find_one({"_id": node_id})
        if not node:
            return []

        # Extract related node IDs
        related_ids = []
        for rel in node.get("relationships", []):
            if relationship_type is None or rel.get("relationship_type") == relationship_type:
                related_ids.append(rel["target_id"])

        # Fetch related nodes
        return list(self.knowledge_graph.find({"_id": {"$in": related_ids}}))

    def update_session(self, session_id: str, updates: dict[str, Any]):
        """
        Update a research session.

        Args:
            session_id: Session ID
            updates: Dictionary of fields to update
        """
        self.sessions.update_one({"_id": session_id}, {"$set": updates})
        logger.info(f"Updated session {session_id}")

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get a research session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session document or None
        """
        return self.sessions.find_one({"_id": session_id})

    def get_past_research(self, query: str, limit: int = 5) -> list[dict]:
        """
        Search for past research sessions similar to the query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of past session documents
        """
        # Simple text search (in production, use MongoDB Atlas Search or text indexes)
        return list(
            self.sessions.find(
                {"query": {"$regex": query, "$options": "i"}},
                {"_id": 1, "query": 1, "timestamp": 1, "sources_collected": 1}
            )
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )

    def close(self):
        """Close MongoDB connection."""
        self.client.close()
        logger.info("MongoDB connection closed")

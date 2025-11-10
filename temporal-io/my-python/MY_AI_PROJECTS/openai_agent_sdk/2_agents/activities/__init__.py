"""MongoDB and deterministic activities for research assistant."""

import hashlib
from datetime import datetime
from typing import Optional
from temporalio import activity
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection

from models import (
    ResearchQuery,
    ResearchContext,
    SourceDocument,
    DataEnrichment,
    KnowledgeGraphNode,
)


class MongoDBClient:
    """MongoDB client singleton."""

    _instance: Optional[MongoClient] = None
    _db = None

    @classmethod
    def get_client(cls, uri: str, database: str):
        """Get or create MongoDB client."""
        if cls._instance is None:
            cls._instance = MongoClient(uri)
            cls._db = cls._instance[database]
            cls._ensure_indexes()
        return cls._db

    @classmethod
    def _ensure_indexes(cls):
        """Create necessary indexes."""
        # Research sources indexes
        cls._db.research_sources.create_index([("query_id", ASCENDING)])
        cls._db.research_sources.create_index([("topics", ASCENDING)])
        cls._db.research_sources.create_index([("credibility_score", DESCENDING)])
        cls._db.research_sources.create_index([("date_collected", DESCENDING)])

        # Knowledge graph indexes
        cls._db.knowledge_graph.create_index([("type", ASCENDING)])
        cls._db.knowledge_graph.create_index([("name", ASCENDING)])

        # Research sessions indexes
        cls._db.research_sessions.create_index([("timestamp", DESCENDING)])
        cls._db.research_sessions.create_index([("query", ASCENDING)])


@activity.defn
async def query_context_from_mongodb(
    query: ResearchQuery,
    mongodb_uri: str,
    mongodb_database: str,
) -> ResearchContext:
    """
    Deterministic activity: Query MongoDB for related past research.

    Retrieves:
    - Related past research sessions
    - Existing sources on similar topics
    - Known topics
    - Identified knowledge gaps
    """
    activity.logger.info(f"Querying MongoDB for context: {query.query}")

    db = MongoDBClient.get_client(mongodb_uri, mongodb_database)

    # Search for related past research
    query_terms = query.query.lower().split()
    related_sessions = list(
        db.research_sessions.find(
            {"query": {"$regex": "|".join(query_terms[:5]), "$options": "i"}},
            limit=5,
        ).sort("timestamp", DESCENDING)
    )

    # Count existing sources
    existing_sources = db.research_sources.count_documents({})

    # Get known topics from past research
    topics_pipeline = [
        {"$unwind": "$topics"},
        {"$group": {"_id": "$topics", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]
    known_topics = [doc["_id"] for doc in db.research_sources.aggregate(topics_pipeline)]

    # Knowledge gaps are topics mentioned but not well-researched
    knowledge_gaps = []
    for session in related_sessions:
        if "knowledge_gaps" in session:
            knowledge_gaps.extend(session["knowledge_gaps"])

    context = ResearchContext(
        related_sessions=[
            {
                "session_id": str(s["_id"]),
                "query": s["query"],
                "sources_count": s.get("sources_collected", 0),
            }
            for s in related_sessions
        ],
        existing_sources=existing_sources,
        known_topics=known_topics[:10],
        knowledge_gaps=list(set(knowledge_gaps[:5])),
    )

    activity.logger.info(
        f"Context retrieved: {len(context.related_sessions)} related sessions, "
        f"{context.existing_sources} existing sources, "
        f"{len(context.known_topics)} known topics"
    )

    return context


@activity.defn
async def store_sources_in_mongodb(
    sources: list[SourceDocument],
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> int:
    """
    Deterministic activity: Store research sources in MongoDB.

    Returns the number of sources stored.
    """
    activity.logger.info(f"Storing {len(sources)} sources in MongoDB")

    db = MongoDBClient.get_client(mongodb_uri, mongodb_database)

    documents = []
    for source in sources:
        doc = {
            "_id": source.source_id,
            "type": source.type,
            "title": source.title,
            "url": source.url,
            "doi": source.doi,
            "authors": source.authors,
            "date_published": source.date_published,
            "date_collected": source.date_collected,
            "credibility_score": source.credibility_score,
            "key_facts": source.key_facts,
            "topics": source.topics,
            "citations": source.citations,
            "abstract": source.abstract,
            "content_summary": source.content_summary,
            "query_id": session_id,
        }
        documents.append(doc)

    if documents:
        result = db.research_sources.insert_many(documents, ordered=False)
        stored_count = len(result.inserted_ids)
    else:
        stored_count = 0

    activity.logger.info(f"Stored {stored_count} sources")
    return stored_count


@activity.defn
async def enrich_and_deduplicate(
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> DataEnrichment:
    """
    Deterministic activity: Enrich data and deduplicate sources.

    Performs:
    - Deduplication based on URL/DOI
    - Cross-referencing between web and academic sources
    - Credibility score calculation
    """
    activity.logger.info(f"Enriching and deduplicating data for session: {session_id}")

    db = MongoDBClient.get_client(mongodb_uri, mongodb_database)

    # Get all sources for this session
    sources = list(db.research_sources.find({"query_id": session_id}))
    total_sources = len(sources)

    # Deduplicate by URL/DOI
    seen = set()
    duplicates = []

    for source in sources:
        identifier = source.get("doi") or source.get("url")
        if identifier:
            if identifier in seen:
                duplicates.append(source["_id"])
            else:
                seen.add(identifier)

    # Remove duplicates
    if duplicates:
        db.research_sources.delete_many({"_id": {"$in": duplicates}})

    deduplicated_count = total_sources - len(duplicates)

    # Create cross-references
    cross_refs = 0
    for source in sources:
        if source["_id"] in duplicates:
            continue

        # Find related sources by topic overlap
        if source.get("topics"):
            related = db.research_sources.find(
                {
                    "_id": {"$ne": source["_id"]},
                    "topics": {"$in": source["topics"]},
                    "query_id": session_id,
                },
                limit=5,
            )

            citations = [r["_id"] for r in related]
            if citations:
                db.research_sources.update_one(
                    {"_id": source["_id"]},
                    {"$set": {"citations": citations}},
                )
                cross_refs += len(citations)

    # Calculate average credibility
    avg_cred_result = db.research_sources.aggregate(
        [
            {"$match": {"query_id": session_id}},
            {"$group": {"_id": None, "avg": {"$avg": "$credibility_score"}}},
        ]
    )
    avg_cred = next(avg_cred_result, {}).get("avg", 0.5)

    enrichment = DataEnrichment(
        total_sources=total_sources,
        deduplicated_sources=deduplicated_count,
        cross_references=cross_refs,
        average_credibility=float(avg_cred),
    )

    activity.logger.info(
        f"Enrichment complete: {deduplicated_count}/{total_sources} unique sources, "
        f"{cross_refs} cross-references, avg credibility: {avg_cred:.2f}"
    )

    return enrichment


@activity.defn
async def store_knowledge_graph(
    nodes: list[KnowledgeGraphNode],
    mongodb_uri: str,
    mongodb_database: str,
) -> int:
    """
    Deterministic activity: Store knowledge graph nodes in MongoDB.

    Returns the number of nodes stored.
    """
    activity.logger.info(f"Storing {len(nodes)} knowledge graph nodes")

    db = MongoDBClient.get_client(mongodb_uri, mongodb_database)

    stored_count = 0
    for node in nodes:
        # Upsert node
        db.knowledge_graph.update_one(
            {"_id": node.node_id},
            {
                "$set": {
                    "type": node.type,
                    "name": node.name,
                    "description": node.description,
                    "relationships": node.relationships,
                    "last_updated": node.last_updated,
                },
                "$setOnInsert": {"first_seen": node.first_seen},
            },
            upsert=True,
        )
        stored_count += 1

    activity.logger.info(f"Stored {stored_count} knowledge graph nodes")
    return stored_count


@activity.defn
async def store_research_session(
    session_data: dict,
    mongodb_uri: str,
    mongodb_database: str,
) -> str:
    """
    Deterministic activity: Store complete research session.

    Returns the session ID.
    """
    activity.logger.info(f"Storing research session: {session_data['session_id']}")

    db = MongoDBClient.get_client(mongodb_uri, mongodb_database)

    session_data["timestamp"] = datetime.utcnow()

    result = db.research_sessions.insert_one(session_data)

    activity.logger.info(f"Session stored with ID: {result.inserted_id}")
    return str(result.inserted_id)

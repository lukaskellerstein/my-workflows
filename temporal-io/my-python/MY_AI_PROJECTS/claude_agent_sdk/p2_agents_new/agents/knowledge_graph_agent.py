import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.sdk_wrapper import Agent

from models.knowledge_graph import (
    KnowledgeGraphNode,
    Relationship,
    NodeType,
    RelationType,
)

from main_workflow.state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


class KnowledgeGraphAgent:
    """Agent for building knowledge graphs from research data."""

    def __init__(self):
        self.logger = logging.getLogger("agent.knowledge_graph")

    async def execute(
        self, state: WorkflowState, db: MongoDBClient
    ) -> List[KnowledgeGraphNode]:
        """Build knowledge graph from all collected research data."""
        self.logger.info("Building knowledge graph from research data")

        # Retrieve all sources for this query
        sources = await db.find_documents("research_sources", {"run_id": state.run_id})

        self.logger.info(f"Processing {len(sources)} sources for knowledge graph")

        # Create summary of all research for Claude
        research_summary = []
        for source in sources:
            research_summary.append(
                {
                    "title": source.get("title", ""),
                    "type": source.get("type", ""),
                    "topics": source.get("topics", []),
                    "key_facts": [
                        fact.get("fact", "") for fact in source.get("key_facts", [])
                    ],
                }
            )

        # Use SDK Agent to extract entities and relationships
        # No MCP servers needed - processes data already in MongoDB
        async with Agent(
            name="knowledge_graph_builder",
            description="Knowledge graph construction specialist that extracts entities and relationships from research data",
            system_prompt="""You are a knowledge graph builder. Analyze the provided research data and extract:
1. Key entities (concepts, people, organizations, events)
2. Relationships between entities
3. Confidence scores for each relationship

Valid relationship types (use only these):
- Generic: related_to, is_a, part_of, contains
- Logical: contradicts, supports, implies, equivalent_to
- Causal: causes, increases, decreases, influences, modulates, prevents, enables
- Temporal: preceded_by, followed_by, concurrent_with
- Attribution: developed_by, created_by, discovered_by
- Domain: applies_to, used_in, based_on, derived_from

Return JSON array of nodes:
[
  {
    "name": "Entity Name",
    "type": "concept|person|organization|event",
    "description": "...",
    "relationships": [
      {
        "target_name": "Other Entity",
        "relationship_type": "one of the valid types above",
        "confidence": 0.85
      }
    ]
  }
]""",
            tools=[],  # No tools needed - pure analysis
        ) as agent:
            response_text = await agent.query(
                f"Research data:\n{json.dumps(research_summary, indent=2)}\n\nExtract knowledge graph."
            )

        # Parse response
        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else "[]"

        try:
            nodes_data = json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse knowledge graph response: {e}")
            nodes_data = []

        # Create knowledge graph nodes
        nodes: List[KnowledgeGraphNode] = []
        node_name_to_id: Dict[str, str] = {}

        # First pass: create nodes
        for node_data in nodes_data:
            node_id = f"node_{len(nodes)}"
            node_name_to_id[node_data.get("name", "")] = node_id

            node = KnowledgeGraphNode(
                id=node_id,
                run_id=state.run_id,
                type=NodeType(node_data.get("type", "concept")),
                name=node_data.get("name", ""),
                description=node_data.get("description", ""),
                relationships=[],
                first_seen=datetime.now(),
                last_updated=datetime.now(),
            )
            nodes.append(node)

        # Second pass: add relationships with correct IDs
        for i, node_data in enumerate(nodes_data):
            relationships = []
            for rel_data in node_data.get("relationships", []):
                target_name = rel_data.get("target_name", "")
                if target_name in node_name_to_id:
                    # Get relationship type, default to related_to if invalid
                    rel_type_str = rel_data.get("relationship_type", "related_to")
                    try:
                        rel_type = RelationType(rel_type_str)
                    except ValueError:
                        self.logger.warning(
                            f"Invalid relationship type '{rel_type_str}', defaulting to 'related_to'"
                        )
                        rel_type = RelationType.RELATED_TO

                    rel = Relationship(
                        target_id=node_name_to_id[target_name],
                        relationship_type=rel_type,
                        confidence=rel_data.get("confidence", 0.7),
                        source_ids=[str(s.get("_id", "")) for s in sources],
                    )
                    relationships.append(rel)

            nodes[i].relationships = relationships

            # Store in MongoDB
            node_dict = nodes[i].model_dump()
            node_dict["first_seen"] = nodes[i].first_seen.isoformat()
            node_dict["last_updated"] = nodes[i].last_updated.isoformat()

            await db.insert_document("knowledge_graph", node_dict)
            self.logger.info(f"Stored knowledge graph node: {nodes[i].name}")

        self.logger.info(f"Knowledge graph complete: {len(nodes)} nodes created")
        return nodes

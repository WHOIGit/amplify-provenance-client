import httpx
from typing import List, Optional, Dict
from datetime import datetime
from urllib.parse import urljoin

from schemas.provenance import (
    NodeCreate, NodeResponse,
    RelationCreate, RelationResponse,
    ProvenanceRecord, ProvenanceResponse,
    ProvType, ProvVerb
)

class ProvenanceClient:
    """Client for interacting with the Provenance API"""
    
    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the API (e.g. "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _url(self, path: str) -> str:
        """Construct full URL from path"""
        return urljoin(f"{self.base_url}/", path.lstrip('/'))

    def create_node(self, 
                   label: str,
                   node_type: ProvType,
                   description: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> NodeResponse:
        """
        Create a new provenance node or get existing one
        
        Args:
            label: Unique identifier for the node
            node_type: Type of node (Entity, Activity, etc)
            description: Optional human-readable description
            metadata: Optional additional attributes
            
        Returns:
            NodeResponse containing the created/existing node details
        """
        node_data = NodeCreate(
            label=label,
            node_type=node_type,
            description=description,
            metadata=metadata or {}
        )
        
        response = self.client.post(
            self._url("/nodes"),
            json=node_data.dict()
            # FIXME .dict is deprecated in favor of .model_dump
        )
        response.raise_for_status()
        return NodeResponse(**response.json())

    def get_node(self, label: str) -> NodeResponse:
        """
        Retrieve a node by its label
        
        Args:
            label: Unique identifier of the node
            
        Returns:
            NodeResponse containing the node details
            
        Raises:
            httpx.HTTPStatusError: If node is not found (404) or other errors
        """
        response = self.client.get(self._url(f"/nodes/{label}"))
        response.raise_for_status()
        return NodeResponse(**response.json())

    def create_relation(self,
                       subject_label: str,
                       verb: ProvVerb,
                       object_label: str,
                       run_id: str,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       metadata: Optional[Dict] = None) -> RelationResponse:
        """
        Create a new provenance relation between existing nodes
        
        Args:
            subject_label: Label of the subject node
            verb: Type of relationship
            object_label: Label of the object node
            run_id: Identifier for grouping related statements
            start_time: Optional start time of the relationship
            end_time: Optional end time of the relationship
            metadata: Optional additional attributes
            
        Returns:
            RelationResponse containing the created relation details
            
        Raises:
            httpx.HTTPStatusError: If nodes not found or other errors
        """
        relation_data = RelationCreate(
            subject_label=subject_label,
            verb=verb,
            object_label=object_label,
            start_time=start_time,
            end_time=end_time,
            metadata=metadata or {}
        )
        
        response = self.client.post(
            self._url("/relations"),
            params={"run_id": run_id},
            json=relation_data.dict(exclude_unset=True)
        )
        response.raise_for_status()
        return RelationResponse(**response.json())

    def get_relations(self, run_id: str) -> List[RelationResponse]:
        """
        Get all relations for a specific run_id
        
        Args:
            run_id: Identifier grouping related provenance statements
            
        Returns:
            List of RelationResponse objects for the given run
        """
        response = self.client.get(
            self._url("/relations"),
            params={"run_id": run_id}
        )
        response.raise_for_status()
        return [RelationResponse(**r) for r in response.json()]

    def create_provenance_record(self,
                               nodes: List[NodeCreate],
                               relations: List[RelationCreate],
                               run_id: str) -> ProvenanceResponse:
        """
        Create multiple nodes and relations in a single transaction
        
        Args:
            nodes: List of nodes to create
            relations: List of relations to create between nodes
            run_id: Identifier for grouping related statements
            
        Returns:
            ProvenanceResponse containing all created relations
            
        Raises:
            httpx.HTTPStatusError: If nodes not found or other errors
        """
        record = ProvenanceRecord(
            nodes=nodes,
            relations=relations,
            run_id=run_id
        )
        
        response = self.client.post(
            self._url("/provenance"),
            json=record.dict()
        )
        response.raise_for_status()
        return ProvenanceResponse(**response.json())

    def close(self):
        """Close the underlying HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Example usage:
"""
from datetime import datetime, timezone

# Initialize client
client = ProvenanceClient("http://localhost:8000")

# Create some nodes
dataset = client.create_node(
    label="dataset-1243",
    node_type=ProvType.ENTITY,
    description="Example dataset"
)

analysis = client.create_node(
    label="analysis-4526",
    node_type=ProvType.ACTIVITY,
    description="Data analysis process"
)

# Create a relation between them
relation = client.create_relation(
    subject_label="dataset-1243",
    verb=ProvVerb.WAS_GENERATED_BY,
    object_label="analysis-4526",
    run_id="experiment-789",
    start_time=datetime.now(timezone.utc)
)

# Get all relations for the run
relations = client.get_relations("experiment-789")

# Create multiple nodes and relations at once
nodes = [
    NodeCreate(label="data-001", node_type=ProvType.ENTITY),
    NodeCreate(label="process-001", node_type=ProvType.ACTIVITY)
]

relations = [
    RelationCreate(
        subject_label="data-001",
        verb=ProvVerb.WAS_GENERATED_BY,
        object_label="process-001"
    )
]

record = client.create_provenance_record(
    nodes=nodes,
    relations=relations,
    run_id="batch-001"
)

# Close client when done
client.close()

# Or use as context manager
with ProvenanceClient("http://localhost:8000") as client:
    node = client.create_node(
        label="test-node",
        node_type=ProvType.ENTITY
    )
"""

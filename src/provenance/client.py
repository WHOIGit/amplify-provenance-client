import httpx
import json
from typing import List, Optional, Dict
from datetime import datetime, timezone
from urllib.parse import urljoin

from schemas.provenance import (
    NodeCreate, NodeResponse,
    RelationCreate, RelationResponse,
    ProvenanceRecord, ProvenanceResponse,
    ProvType, ProvVerb,
    DateTimeEncoder
)

class ProvenanceClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _url(self, path: str) -> str:
        return urljoin(f"{self.base_url}/", path.lstrip('/'))

    def _ensure_utc(self, dt: Optional[datetime]) -> Optional[datetime]:
        if dt and dt.tzinfo != timezone.utc:
            return dt.astimezone(timezone.utc)
        return dt

    def _serialize_json(self, obj: dict) -> str:
        return json.dumps(obj, cls=DateTimeEncoder)

    def create_node(self, 
                   label: str,
                   node_type: ProvType,
                   description: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> NodeResponse:
        node_data = NodeCreate(
            label=label,
            node_type=node_type,
            description=description,
            metadata=metadata or {}
        )
        
        response = self.client.post(
            self._url("/nodes"),
            content=self._serialize_json(node_data.model_dump(exclude_unset=True))
        )
        response.raise_for_status()
        return NodeResponse.model_validate(response.json())

    def get_node(self, label: str) -> NodeResponse:
        response = self.client.get(self._url(f"/nodes/{label}"))
        response.raise_for_status()
        return NodeResponse.model_validate(response.json())

    def create_relation(self,
                       subject_label: str,
                       verb: ProvVerb,
                       object_label: str,
                       run_id: str,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       metadata: Optional[Dict] = None) -> RelationResponse:
        relation_data = RelationCreate(
            subject_label=subject_label,
            verb=verb,
            object_label=object_label,
            start_time=self._ensure_utc(start_time),
            end_time=self._ensure_utc(end_time),
            metadata=metadata or {}
        )
        
        response = self.client.post(
            self._url("/relations"),
            params={"run_id": run_id},
            content=self._serialize_json(relation_data.model_dump(exclude_unset=True))
        )
        response.raise_for_status()
        return RelationResponse.model_validate(response.json())

    def get_relations(self, run_id: str) -> List[RelationResponse]:
        response = self.client.get(
            self._url("/relations"),
            params={"run_id": run_id}
        )
        response.raise_for_status()
        return [RelationResponse.model_validate(r) for r in response.json()]

    def create_provenance_record(self,
                               nodes: List[NodeCreate],
                               relations: List[RelationCreate],
                               run_id: str) -> ProvenanceResponse:
        record = ProvenanceRecord(
            nodes=nodes,
            relations=relations,
            run_id=run_id
        )
        
        response = self.client.post(
            self._url("/provenance"),
            content=self._serialize_json(record.model_dump(exclude_unset=True))
        )
        response.raise_for_status()
        return ProvenanceResponse.model_validate(response.json())

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
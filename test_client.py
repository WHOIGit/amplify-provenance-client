from datetime import datetime, timezone
from provenance.client import ProvenanceClient
from provenance.client import ProvType, ProvVerb

def main():
    # Initialize client - adjust URL to match your server
    with ProvenanceClient("http://localhost:8000/api") as client:
        # Create test nodes
        def apply_label_prefix(label):
            return f"test1-{label}"
        
        dataset = client.create_node(
            label=apply_label_prefix("test-dataset-001"),
            node_type=ProvType.ENTITY,
            description="Test dataset",
            metadata={"format": "csv", "size": 1024}
        )
        print(f"Created dataset node: {dataset.label}")

        process = client.create_node(
            label=apply_label_prefix("test-process-001"),
            node_type=ProvType.ACTIVITY,
            description="Test analysis process",
            metadata={"version": "1.0"}
        )
        print(f"Created process node: {process.label}")

        # Create relation
        run_id = apply_label_prefix("test-run-001")

        relation = client.create_relation(
            subject_label=dataset.label,
            verb=ProvVerb.WAS_GENERATED_BY,
            object_label=process.label,
            run_id=run_id,
            start_time=datetime.now(timezone.utc)
        )
        print(f"Created relation: {relation.subject_label} {relation.verb} {relation.object_label}")

        # Fetch relations
        relations = client.get_relations(run_id)
        print(f"\nFound {len(relations)} relations for run ${run_id}:")
        for r in relations:
            print(f"- {r.subject_label} {r.verb} {r.object_label}")

if __name__ == "__main__":
    main()
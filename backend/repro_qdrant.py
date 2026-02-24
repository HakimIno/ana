from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np

client = QdrantClient(":memory:")
collection_name = "test"
client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
    sparse_vectors_config={"text-sparse": models.SparseVectorParams()}
)

query_vector = [0.1, 0.2, 0.3, 0.4]
query_filter = models.Filter(must=[
    models.FieldCondition(key="metadata.filename", match=models.MatchValue(value="test.csv"))
])

print("Attempting query_points with query_filter...")
try:
    prefetch = [
        models.Prefetch(query=query_vector, limit=5),
    ]
    results = client.query_points(
        collection_name=collection_name,
        prefetch=prefetch,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        limit=5
    )
    print("Success with query_filter")
except Exception as e:
    print(f"Error with query_filter: {e}")

print("\nAttempting query_points with filter...")
try:
    results = client.query_points(
        collection_name=collection_name,
        prefetch=prefetch,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        filter=query_filter,
        limit=5
    )
    print("Success with filter")
except Exception as e:
    print(f"Error with filter: {e}")

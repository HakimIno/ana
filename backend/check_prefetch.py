from qdrant_client import QdrantClient
from qdrant_client.http import models
import inspect

print("Args for models.Prefetch:", inspect.signature(models.Prefetch).parameters.keys())
print("Args for models.Prefetch.__init__:", inspect.signature(models.Prefetch.__init__).parameters.keys())

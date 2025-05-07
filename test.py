import chromadb
import json
import numpy as np

chroma_client = chromadb.PersistentClient(path="./chroma_last")
collection = chroma_client.get_or_create_collection(name="anime_clip_embeddings")
res = collection.peek()
print(collection.get(
    documents=["Abashiri"] ,
    include=['embeddings','documents']
))
# Convert ndarrays to lists
def convert_ndarray(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

json.dump(res, open("db_struct.json", "w"), indent=4, default=convert_ndarray)
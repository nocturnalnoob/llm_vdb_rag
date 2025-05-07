import pickle
import chromadb
import numpy as np
from tqdm import tqdm

# Load the embeddings from pickle file
with open("clip_embeddings_fixed.pkl", "rb") as f:
    embeddings_data = pickle.load(f)

print("Type of embeddings_data:", type(embeddings_data))
print("Keys in embeddings_data:", embeddings_data.keys() if isinstance(embeddings_data, dict) else "Not a dictionary")
print("Type of image_embeddings:", type(embeddings_data["image_embeddings"]))
print("Shape of image_embeddings:", embeddings_data["image_embeddings"].shape if isinstance(embeddings_data["image_embeddings"], np.ndarray) else "No shape")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_last")

# Create or get collection
collection = chroma_client.get_or_create_collection(
    name="anime_clip_embeddings"
)

# # Extract data from embeddings_data
# character_names = []
# embeddings = []
# metadata = []

# # Process embeddings in batches
# batch_size = 100

# # Get all character names from character_names list
# all_characters = embeddings_data["character_names"]

# for i in tqdm(range(0, len(all_characters), batch_size), desc="Loading embeddings into ChromaDB"):
#     batch_characters = all_characters[i:i + batch_size]
    
#     batch_names = []
#     batch_embeddings = []
#     batch_metadata = []
    
#     for idx, char_name in enumerate(batch_characters):
#         # Get image embedding
#         image_embedding = embeddings_data["image_embeddings"][i + idx]
        
#         if image_embedding is not None:
#             # Add to batch
#             batch_names.append(char_name)
#             batch_embeddings.append(image_embedding.tolist())  # Convert numpy array to list for ChromaDB
#             batch_metadata.append({
#                 "file_path": embeddings_data["image_paths"][i + idx],
#                 "description": ""  # No description available in this data structure
#             })
    
#     if batch_names:
#         # Add batch to ChromaDB
#         collection.add(
#             documents=batch_names,  # Using character names as documents
#             embeddings=batch_embeddings,
#             metadatas=batch_metadata,
#             ids=[f"char_{idx}" for idx in range(i, i + len(batch_names))]
#         )

# print(f"Successfully loaded {collection.count()} embeddings into ChromaDB")

# Test a simple query
results = collection.query(
    query_embeddings=[embeddings_data["image_embeddings"][0].tolist()],  # Convert to list for first character
    n_results=5
)
print("\nTest query results:")
print(f"Found {len(results['documents'][0])} matches")
for doc, score in zip(results['documents'][0], results['distances'][0]):
    print(f"Character: {doc}, Distance: {score:.4f}")
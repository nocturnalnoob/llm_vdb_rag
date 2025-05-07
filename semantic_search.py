from transformers import CLIPProcessor, CLIPModel
import torch
import chromadb
import numpy as np
from typing import List, Tuple, Optional

class AnimeImageSearch:
    def __init__(self, model_name: str = "openai/clip-vit-large-patch14-336"):
        # Initialize device (CUDA if available, else CPU)
        self.device = "xpu" if torch.xpu.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load CLIP model and processor
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name , use_fast=True)
        self.model.eval()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_last")
        self.collection = self.chroma_client.get_collection("anime_clip_embeddings")

    def encode_text(self, text: str) -> List[float]:
        """Encode text query into CLIP embedding"""
        inputs = self.processor(text=[text], return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            
        # Move to CPU and normalize
        embedding = text_features[0].cpu().numpy()
        normalized_embedding = embedding / np.linalg.norm(embedding)
        return normalized_embedding.tolist()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """
        Search for anime characters based on text description
        Returns: List of (character_name, image_filename, similarity_score)
        """
        # Encode query text
        query_embedding = self.encode_text(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances"]
        )
        
        # Format results
        character_results = []
        for doc, dist in zip(results['documents'][0], results['distances'][0]):
            # Convert distance to similarity score (1 - normalized_distance)
            similarity = 1 - (dist / 2)  # Assuming normalized distance
            character_results.append((doc, doc.replace(' ', '_'), similarity))
            
        return character_results

def main():
    # Example usage
    searcher = AnimeImageSearch()
    
    # Example query
    query = "red hair boy who looks like Akibara renji and has goggles on face"
    results = searcher.search(query, top_k=5)
    
    print(f"\nSearch results for: '{query}'")
    print("-" * 50)
    for char_name, image_id, score in results:
        print(f"Character: {char_name}")
        print(f"Image: {image_id}")
        print(f"Similarity Score: {score:.3f}")
        print("-" * 50)

if __name__ == "__main__":
    main()
    
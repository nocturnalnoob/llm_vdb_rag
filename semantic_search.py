import aiohttp
import asyncio
from typing import Dict, Any , List , Tuple
from transformers import CLIPProcessor, CLIPModel
import torch
import chromadb
import numpy as np
class AnimeImageSearch:
    def __init__(self, model_name: str = "openai/clip-vit-large-patch14-336"):
        # Initialize device (CUDA if available, else CPU)
        self.device = "xpu" if torch.xpu.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load CLIP model and processor
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
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


    async def get_character_info(self, character_name: str) -> Dict[Any, Any]:
        """Fetch character information from Jikan API"""
        # Clean up the name for search
        search_name = character_name.replace(',', '').strip()
        
        async with aiohttp.ClientSession() as session:
            # Use Jikan v4 API
            url = f"https://api.jikan.moe/v4/characters?q={search_name}&limit=1"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        import json
                        with open("data.json" , "w") as f:
                            json.dump(data , f , indent=4)
                        if data['data']:
                            return {
                                'mal_id': data['data'][0]['mal_id'],
                                'url': data['data'][0]['url'],
                                'image_url': data['data'][0]['images']['jpg']['image_url'],
                                'name': data['data'][0]['name']
                            }
            except Exception as e:
                print(f"Error fetching data for {character_name}: {e}")
            return None

    async def search_with_jikan(self, query: str, top_k: int = 5):
        """Search characters and enrich results with Jikan data"""
        base_results = self.search(query, top_k)
        enriched_results = []

        # Need to rate limit Jikan API calls (4 requests/second)
        for char_name, image_id, score in base_results:
            # Wait 0.25 seconds between requests
            await asyncio.sleep(0.25)
            jikan_data = await self.get_character_info(char_name)
            
            enriched_results.append({
                'character_name': char_name,
                'image_id': image_id,
                'similarity_score': score,
                'jikan_data': jikan_data
            })
            
        return enriched_results

def main():
    searcher = AnimeImageSearch()
    
    # Example query
    query = "a small boy with a big smile and green clothes"
    
    # Run async search
    async def run_search():
        results = await searcher.search_with_jikan(query, top_k=5)
        
        print(f"\nSearch results for: '{query}'")
        print("-" * 50)
        for result in results:
            print(f"Character: {result['character_name']}")
            print(f"Image: {result['image_id']}")
            print(f"Similarity Score: {result['similarity_score']:.3f}")
            if result['jikan_data']:
                print(f"MAL Link: {result['jikan_data']['url']}")
                print(f"MAL Image: {result['jikan_data']['image_url']}")
            print("-" * 50)

    # Run the async function
    asyncio.run(run_search())

if __name__ == "__main__":
    main()
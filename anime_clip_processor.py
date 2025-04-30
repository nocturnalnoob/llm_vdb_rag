import os
from pathlib import Path
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions
import concurrent.futures
from typing import List, Tuple
import numpy as np

# Check device (XPU if available, else CPU)
device = torch.device("xpu" if torch.xpu.is_available() else "cpu")
print(f"Using device: {device}")

def load_and_process_image(image_path: str, processor: CLIPProcessor, model: CLIPModel, device: torch.device) -> Tuple[str, str, List[float]]:
    file_name = Path(image_path).stem
    character_name = file_name.replace('_', ' ')

    try:
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        inputs = processor(images=image, return_tensors="pt")
        
        # Move tensors to device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate embedding
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)

        # Move back to CPU for normalization and storage
        embedding = image_features[0].cpu().numpy()
        normalized_embedding = embedding / np.linalg.norm(embedding)

        return character_name, file_name, normalized_embedding.tolist()
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None

def main():
    model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)

    # Move model to device (XPU/CPU)
    model.to(device)
    model.eval()

    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    collection = chroma_client.get_or_create_collection(
        name="anime_clip_embeddings",
        embedding_function=embedding_function
    )

    # Get list of image files
    image_dir = "./images"
    image_files = [
        os.path.join(image_dir, f) for f in os.listdir(image_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    processed_count = 0
    batch_size = 32  # Adjust as needed

    # Use ThreadPoolExecutor for I/O bound tasks, but consider ProcessPoolExecutor for CPU-bound preprocessing if needed
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for i in tqdm(range(0, len(image_files), batch_size), desc="Processing batches"):
            batch_files = image_files[i:i + batch_size]

            futures = [
                executor.submit(load_and_process_image, img_path, processor, model, device)
                for img_path in batch_files
            ]

            batch_data = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    batch_data.append(result)

            if batch_data:
                character_names, file_ids, embeddings = zip(*batch_data)
                try:
                    collection.add(
                        documents=list(character_names),
                        ids=list(file_ids),
                        embeddings=list(embeddings)
                    )
                    processed_count += len(batch_data)
                except Exception as e:
                    print(f"Error adding batch to ChromaDB: {str(e)}")

    print(f"\nProcessing complete! Total images processed: {processed_count}")
    print(f"Collection count: {collection.count()}")

if __name__ == "__main__":
    main()

import os
import pickle
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

model_name = "openai/clip-vit-base-patch32"
model = CLIPModel.from_pretrained(model_name)
processor = CLIPProcessor.from_pretrained(model_name)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

EMBEDDING_FILE = "embeddings.pkl"
SIMILARITY_THRESHOLD = 0.80

def get_image_embeddings(image_path: str):
    """
    Compute normalized image embeddings using CLIP.
    """
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
    # Normalize the embeddings for easier comparison
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features.cpu().numpy()  # Convert to numpy for easy storage in pickle

def is_duplicate_embedding(new_emb, existing_emb, threshold=SIMILARITY_THRESHOLD):
    """
    Check if the new embedding is sufficiently similar to an existing embedding.
    """
    # new_emb and existing_emb are numpy arrays of shape (1, 512)
    new_emb_t = torch.from_numpy(new_emb)
    existing_emb_t = torch.from_numpy(existing_emb)
    similarity = torch.nn.functional.cosine_similarity(new_emb_t, existing_emb_t, dim=-1)
    # similarity will be a single value since both are (1, 512)
    return similarity.item() >= threshold

def score_image(image_path: str, text_prompts=["beautiful, high-quality image, aesthetic, meaning full and motivating/sptirual"]):
    """
    Compute similarity score between image and text prompts.
    """
    image = Image.open(image_path).convert("RGB")
    inputs = processor(text=text_prompts, images=image, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    image_embeds = outputs.image_embeds
    text_embeds = outputs.text_embeds
    similarity = torch.cosine_similarity(image_embeds, text_embeds, dim=-1).mean().item()
    return similarity

def load_embeddings():
    """
    Load embeddings dictionary from EMBEDDING_FILE if it exists.
    Returns a dict: {image_path: embedding (numpy array)}
    """
    if os.path.exists(EMBEDDING_FILE):
        with open(EMBEDDING_FILE, "rb") as f:
            embeddings_dict = pickle.load(f)
    else:
        embeddings_dict = {}
    return embeddings_dict

def save_embeddings(embeddings_dict):
    """
    Save embeddings dictionary to EMBEDDING_FILE.
    """
    with open(EMBEDDING_FILE, "wb") as f:
        pickle.dump(embeddings_dict, f)

def select_top_images(image_paths, top_k=10):
    # Load existing embeddings
    embeddings_dict = load_embeddings()

    scored_images = []

    for img_path in image_paths:
        try:
            # Check if embedding already exists for this image
            if img_path in embeddings_dict:
                # We could choose to skip scoring if we trust our previous scoring
                # For demonstration, let's assume we still score again based on text prompts.
                # If you have already stored scores, you can skip this step.
                existing_emb = embeddings_dict[img_path]
            else:
                # Compute new embedding
                new_emb = get_image_embeddings(img_path)

                # Check for duplicates in existing embeddings
                # To do this efficiently, consider only checking against a subset or
                # store embeddings in a separate structure. For now, we do a simple loop.
                duplicate_found = False
                for stored_emb in embeddings_dict.values():
                    if is_duplicate_embedding(new_emb, stored_emb):
                        print(f"Skipping {img_path}: similar to an existing image.")
                        duplicate_found = True
                        break

                if duplicate_found:
                    continue

                # If not a duplicate, store the embedding
                embeddings_dict[img_path] = new_emb
                save_embeddings(embeddings_dict)  # Save after each insertion if you prefer

            # Score the image
            score = score_image(img_path)
            scored_images.append((img_path, score))

        except Exception as e:
            print(f"Error scoring image {img_path}: {e}")

    # Sort and return top_k
    scored_images.sort(key=lambda x: x[1], reverse=True)
    return [img[0] for img in scored_images[:top_k]]

# Example usage:
# top_images = select_top_images(["image1.jpg", "image2.jpg", "image3.jpg"], top_k=2)
# print(top_images)

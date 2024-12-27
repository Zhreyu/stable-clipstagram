import os
import sys
import time
import torch
from PIL import Image
from dotenv import load_dotenv
from diffusers import StableDiffusion3Pipeline
from instagrapi import Client

from utils.fetch_image import fetch_random_images_from_carousels
from ai.image_selector import select_top_images
from ai.caption_generator import generate_caption
from utils.image_utils import cleanup_temp_directory

load_dotenv()

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
SOURCE_ACCOUNTS = os.getenv("SOURCE_ACCOUNTS").split(",")

def generate_images_stable_diffusion(prompt: str, num_images: int = 4) -> list[str]:
    """
    Generate multiple images using Stable Diffusion 3.
    
    Args:
        prompt (str): Text prompt for image generation
        num_images (int): Number of images to generate
        
    Returns:
        list[str]: List of paths to generated images
    """
    print(f"Initializing Stable Diffusion with prompt: {prompt}")
    
    # Initialize pipeline
    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3-medium-diffusers",
        torch_dtype=torch.float16
    )
    pipe = pipe.to("cuda")
    
    generated_paths = []
    os.makedirs("temp", exist_ok=True)
    
    for i in range(num_images):
        try:
            image = pipe(
                f"A monochromatic image which captures : {prompt}",
                negative_prompt="Text on image, Blur, Pixelated, Low quality",
                num_inference_steps=50,
                guidance_scale=3.0,
            ).images[0]
            
            # Save the image
            filepath = os.path.join("temp", f"sd_gen_{i}.png")
            image.save(filepath)
            generated_paths.append(filepath)
            print(f"Generated image {i+1}/{num_images}")
            
        except Exception as e:
            print(f"Error generating image {i+1}: {e}")
            continue
            
    return generated_paths

def main():
    # Fetch reference images for caption generation
    desired_count = 10
    unique_images = set()
    max_attempts = 10
    attempt = 0

    while len(unique_images) < desired_count and attempt < max_attempts:
        print(f"Attempt {attempt+1}: Fetching reference images...")
        new_images = fetch_random_images_from_carousels(SOURCE_ACCOUNTS)
        unique_images.update(new_images)
        attempt += 1

    if len(unique_images) < desired_count:
        print(f"Not enough unique images after {attempt} attempts. Exiting.")
        cleanup_temp_directory()
        sys.exit(1)

    # Select top images and generate caption
    image_paths = list(unique_images)
    print("Selecting top reference images using AI scoring...")
    selected_images = select_top_images(image_paths, top_k=6)

    print("Generating caption from selected images...")
    caption = generate_caption(selected_images)
    print("Generated Caption:", caption)

    # Generate multiple images using Stable Diffusion
    print("Generating images using Stable Diffusion...")
    generated_images = generate_images_stable_diffusion(caption, num_images=4)
    if not generated_images:
        print("Failed to generate any images. Exiting.")
        cleanup_temp_directory()
        sys.exit(1)

    # Select the best generated image using the same scoring method
    print("Selecting the best generated image...")
    best_generated = select_top_images(generated_images, top_k=1)[0]

    # Post to Instagram
    print("Logging into Instagram...")
    cl = Client()
    try:
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    except Exception as e:
        print(f"Failed to login to Instagram: {e}")
        cleanup_temp_directory()
        sys.exit(1)

    print("Posting the best generated image to Instagram...")
    try:
        media = cl.photo_upload(best_generated, caption=caption)
        print("Successfully posted image:", media.dict())
    except Exception as e:
        print(f"Error posting image: {e}")

    cleanup_temp_directory()
    print("Done.")

if __name__ == "__main__":
    main()
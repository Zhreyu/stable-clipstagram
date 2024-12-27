import os
import base64
from pathlib import Path
from ollama import chat

def get_image_data_url(image_file: str) -> str:
    return image_file


def generate_caption(image_paths):
    descriptions = []

    # Step 1: Use llava:13b to get a description for each image
    for img_path in image_paths:
        # Send one image at a time to llava:13b
        # Prompt the model to describe the image in detail
        response = chat(
            model='llava:13b',
            messages=[
                {
                    "role": "user",
                    "content": "Describe this image in detail.",
                    "images": [get_image_data_url(img_path)]
                },
            ]
        )

        # The response should contain the model's message content
        # print(response)
        description = response['message']['content'].strip()
        if description:
            descriptions.append(description)

    if not descriptions:
        print("No descriptions generated. Cannot produce a caption.")
        return ""

    # Step 2: Use llama3.2 (or llama3.2:1b) to generate a caption based on these descriptions.
    combined_description = "\n".join(descriptions)
    caption_prompt = (
        f"Below are descriptions of several images:\n\n{combined_description}\n\n"
        "Please craft a short, visually descriptive and engaging Instagram caption that reflects the collective theme of these images, "
        "and includes a few relevant hashtags. Answer only with caption content."
    )

    caption_response = chat(
        model='llama3.2:1b',  # or 'llama3.2:1b' if that is the correct tag
        messages=[
            {
                "role": "user",
                "content": caption_prompt
            }
        ]
    )

    caption = caption_response['message']['content'].strip()
    print(caption)
    return caption

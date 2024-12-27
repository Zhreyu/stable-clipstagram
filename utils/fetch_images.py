import os
import random
import requests
from pathlib import Path
from instagrapi import Client

TEMP_DIR = "temp_images"
USERNAME = "your_username"
PASSWORD = "your_password"

def fetch_random_images_from_carousels(source_accounts, max_posts_per_account=10):
    Path(TEMP_DIR).mkdir(exist_ok=True)

    cl = Client()
    cl.login(USERNAME, PASSWORD)
    print("Login successful!")

    selected_image_paths = []
    random.shuffle(source_accounts)

    for acc in source_accounts:
        print(f"Processing account: {acc}")
        try:
            # Try a different method if user_id_from_username fails
            # user_id = cl.user_id_from_username(acc)
            user_info = cl.user_info_by_username(acc)
            user_id = user_info.pk
        except Exception as e:
            print(f"Error fetching user ID for {acc}: {e}")
            continue

        try:
            medias = cl.user_medias(user_id, amount=max_posts_per_account)
        except Exception as e:
            print(f"Error fetching medias for {acc}: {e}")
            continue

        for media in medias:
            # Check if media is a carousel (media_type=8)
            if media.media_type != 8:
                continue
            if not media.resources:
                continue

            selected_node = random.choice(media.resources)
            
            # Use display_url or thumbnail_url instead of media_url
            img_url = getattr(selected_node, 'display_url', None)
            if not img_url:
                img_url = getattr(selected_node, 'thumbnail_url', None)
            
            if not img_url:
                print("No valid image URL found for this carousel resource, skipping.")
                continue

            filename = os.path.join(TEMP_DIR, f"{acc}_{media.pk}_{random.randint(1000,9999)}.jpg")

            try:
                r = requests.get(img_url, stream=True)
                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    selected_image_paths.append(filename)
                    print(f"Downloaded {filename}")
                else:
                    print(f"Failed to download image from {img_url}, status: {r.status_code}")
            except Exception as e:
                print(f"Error downloading image from {img_url}: {e}")
            
            source_accounts = [i for i in source_accounts if i != acc]

    print(f"Total selected images: {len(selected_image_paths)}")
    return selected_image_paths

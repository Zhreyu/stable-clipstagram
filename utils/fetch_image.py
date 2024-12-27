import os
import random
import requests
from pathlib import Path
import instaloader

TEMP_DIR = "temp_images"

def fetch_random_images_from_carousels(source_accounts, max_posts_per_account=10):
    Path(TEMP_DIR).mkdir(exist_ok=True)

    L = instaloader.Instaloader(download_pictures=True,
                                download_videos=False,
                                download_video_thumbnails=False,
                                compress_json=False)
    selected_image_paths = []
    random.shuffle(source_accounts)
    for acc in source_accounts:
        if(len(os.listdir(TEMP_DIR))>15):
            break
        print(f"Processing account: {acc}")
        try:
            profile = instaloader.Profile.from_username(L.context, acc)
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"Profile {acc} does not exist. Skipping.")
            continue
        except Exception as e:
            print(f"Error fetching profile {acc}: {e}")
            continue

        posts = profile.get_posts()
        posts_list = []
        for i, p in enumerate(posts):
            if i >= max_posts_per_account:
                break
            posts_list.append(p)

        for post in posts_list:
            # Check if this post is a carousel (sidecar)
            if post.typename != "GraphSidecar":
                continue

            sidecar_nodes = list(post.get_sidecar_nodes())
            if not sidecar_nodes:
                continue

            # Randomly pick one node from the carousel
            selected_node = random.choice(sidecar_nodes)
            display_url = selected_node.display_url
            if not display_url:
                continue

            # Use a unique filename for each fetched image
            # Include post.shortcode and a random suffix to avoid collisions
            filename = os.path.join(TEMP_DIR, f"{acc}_{post.shortcode}_{random.randint(1000,9999)}.jpg")

            try:
                r = requests.get(display_url, stream=True)
                if r.status_code == 200:
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    selected_image_paths.append(filename)
                else:
                    print(f"Failed to download image from {display_url}")
            except Exception as e:
                print(f"Error downloading image: {e}")

    print(f"Total selected images: {len(selected_image_paths)}")
    return selected_image_paths

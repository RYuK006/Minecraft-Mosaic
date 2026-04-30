import urllib.request
import json
import os
from concurrent.futures import ThreadPoolExecutor

branch = '26.2-snapshot-5'
repo = 'InventivetalentDev/minecraft-assets'
out_dir = r'C:\Users\hp\Desktop\Minecraft_project\assets_repo'

os.makedirs(out_dir, exist_ok=True)

# Fetch the tree
api_url = f'https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1'
print(f"Fetching tree from {api_url}...")

req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
except Exception as e:
    print("Error fetching tree:", e)
    exit(1)

# Find block textures
prefix = 'assets/minecraft/textures/block/'
files_to_download = []
for item in data.get('tree', []):
    if item['path'].startswith(prefix) and item['path'].endswith('.png'):
        files_to_download.append(item['path'])

print(f"Found {len(files_to_download)} block textures. Downloading...")

def download_file(path):
    filename = os.path.basename(path)
    out_path = os.path.join(out_dir, filename)
    raw_url = f'https://raw.githubusercontent.com/{repo}/{branch}/{path}'
    try:
        req = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            with open(out_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Failed to download {path}: {e}")
        return False

# Download concurrently
downloaded = 0
with ThreadPoolExecutor(max_workers=20) as executor:
    results = executor.map(download_file, files_to_download)
    for r in results:
        if r:
            downloaded += 1
            if downloaded % 50 == 0:
                print(f"Downloaded {downloaded}/{len(files_to_download)}")

print(f"Done! Successfully downloaded {downloaded} files to {out_dir}")

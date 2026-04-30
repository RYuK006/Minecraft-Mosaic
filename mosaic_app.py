import os
import numpy as np
from PIL import Image
import gradio as gr
from scipy.spatial import KDTree

BLOCKS_DIR = r"C:\Users\hp\Desktop\Minecraft_project\assets_repo"

# Cache for loaded blocks
cached_tree = None
cached_blocks = None
cached_colors = None

def load_blocks():
    global cached_tree, cached_blocks, cached_colors
    if cached_tree is not None:
        return
    
    print("Loading block textures...")
    blocks = []
    colors = []
    
    if not os.path.exists(BLOCKS_DIR):
        print(f"Error: Directory {BLOCKS_DIR} not found. Please ensure blocks are downloaded.")
        return
        
    for filename in os.listdir(BLOCKS_DIR):
        if not filename.endswith('.png'):
            continue
            
        path = os.path.join(BLOCKS_DIR, filename)
        try:
            img = Image.open(path).convert("RGBA")
            # Force block to be exactly 16x16. 
            # If animated (e.g. 16x32), just crop the first frame
            if img.width != 16 or img.height != 16:
                img = img.crop((0, 0, 16, 16))
                
            arr = np.array(img)
            
            # Filter mostly transparent images
            # alpha channel is index 3
            alpha = arr[:,:,3]
            if np.mean(alpha) < 250:
                continue
                
            # Compute average RGB color across all solid pixels
            r = np.mean(arr[:,:,0])
            g = np.mean(arr[:,:,1])
            b = np.mean(arr[:,:,2])
            
            # Convert to RGB image to discard alpha channel for output
            rgb_img = img.convert("RGB")
            
            blocks.append(rgb_img)
            colors.append((r, g, b))
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
    if not blocks:
        print("No valid blocks found!")
        return

    cached_blocks = blocks
    cached_colors = np.array(colors)
    cached_tree = KDTree(cached_colors)
    print(f"Loaded {len(blocks)} solid blocks.")

def generate_mosaic(input_image, resolution):
    load_blocks()
    
    if cached_tree is None:
        raise ValueError("Blocks not loaded correctly. Check the assets_repo directory.")

    # Convert Gradio image to PIL
    if isinstance(input_image, np.ndarray):
        img = Image.fromarray(input_image)
    else:
        img = input_image
        
    img = img.convert("RGB")
    
    # Target dimensions
    w, h = img.size
    aspect_ratio = h / w
    target_w = int(resolution)
    target_h = int(target_w * aspect_ratio)
    
    print(f"Resizing input image to {target_w}x{target_h} blocks.")
    img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    img_arr = np.array(img_resized)
    
    # Output dimensions
    block_size = 16
    out_w = target_w * block_size
    out_h = target_h * block_size
    out_img = Image.new("RGB", (out_w, out_h))
    
    # Query nearest neighbors
    flat_pixels = img_arr.reshape(-1, 3)
    distances, indices = cached_tree.query(flat_pixels)
    
    # Reconstruct mosaic
    idx = 0
    for y in range(target_h):
        for x in range(target_w):
            block_idx = indices[idx]
            block_img = cached_blocks[block_idx]
            out_img.paste(block_img, (x * block_size, y * block_size))
            idx += 1
            
    print("Mosaic generated successfully.")
    return out_img

with gr.Blocks(title="Minecraft Mosaic Generator") as demo:
    gr.Markdown("# ⛏️ Minecraft Mosaic Generator")
    gr.Markdown("Upload an image to convert it into a Minecraft block mosaic!")
    
    with gr.Row():
        with gr.Column():
            img_input = gr.Image(label="Input Image", type="pil")
            res_slider = gr.Slider(minimum=10, maximum=300, step=10, value=100, label="Resolution (blocks wide)")
            generate_btn = gr.Button("Generate Mosaic", variant="primary")
        
        with gr.Column():
            img_output = gr.Image(label="Minecraft Mosaic Output", type="pil", format="png")
            
    generate_btn.click(fn=generate_mosaic, inputs=[img_input, res_slider], outputs=img_output)

if __name__ == "__main__":
    demo.launch()

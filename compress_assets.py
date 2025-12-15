import os
from PIL import Image

def compress_images(directory, quality=80):
    total_saved = 0
    extensions = {'.png', '.jpg', '.jpeg'}
    
    print(f"Scanning directory: {directory}")
    
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} does not exist!")
        return

    files = os.listdir(directory)
    print(f"Found {len(files)} files in directory.")

    for filename in files:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in extensions:
            # print(f"Ignoring non-image: {filename}")
            continue
            
        filepath = os.path.join(directory, filename)
        
        try:
            # Get original size
            original_size = os.path.getsize(filepath)
            
            with Image.open(filepath) as img:
                # Preserve transparency for PNGs
                if ext == '.png':
                    # PNG optimization
                    img.save(filepath, 'PNG', optimize=True, compress_level=9)
                else:
                    # JPEG optimization
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    img.save(filepath, 'JPEG', quality=quality, optimize=True)
            
            # Get new size
            new_size = os.path.getsize(filepath)
            saved = original_size - new_size
            total_saved += saved
            
            if saved > 0:
                print(f"Compressed {filename}: {original_size/1024:.1f}KB -> {new_size/1024:.1f}KB (Saved {saved/1024:.1f}KB)")
            elif saved == 0:
                print(f"No change {filename}")
            else:
                print(f"Increased {filename} (kept new): {original_size/1024:.1f}KB -> {new_size/1024:.1f}KB")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\nTotal space saved: {total_saved/1024/1024:.2f} MB")

if __name__ == "__main__":
    # Ensure we point to the right place regardless of where we run from
    # Assumes script is in root (shengdan) and frontend is shengdan/frontend
    
    # Use absolute path logic carefully
    script_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(script_path)
    # The images are in frontend/images
    images_dir = os.path.join(root_dir, "frontend", "images")
    
    compress_images(images_dir)

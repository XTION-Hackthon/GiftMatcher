import os
from rembg import remove
from PIL import Image
import io

# Source files mapping
sources = [
    ("7340792be847e128799d1689daab1630.jpg", "decoration_1.png"),
    ("5c850ea2fcea6ba839b1d5b23ca3fe6a.png", "decoration_2.png"),
    ("3adfb2a2babd428dc05113735b23241b.jpg", "decoration_3.png"),
    ("6b05888eaebb91bc17fb01d1d0a0785a.jpg", "decoration_4.png")
]

# Paths
root_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(root_dir, "frontend")

if not os.path.exists(frontend_dir):
    os.makedirs(frontend_dir)

for src_name, dest_name in sources:
    src_path = os.path.join(root_dir, src_name)
    dest_path = os.path.join(frontend_dir, dest_name)
    
    print(f"Processing {src_name} -> {dest_name}...")
    
    try:
        if not os.path.exists(src_path):
            print(f"Error: Source file {src_path} not found.")
            continue
            
        with open(src_path, 'rb') as i:
            input_data = i.read()
            output_data = remove(input_data)
            
            with open(dest_path, 'wb') as o:
                o.write(output_data)
        
        print(f"Saved to {dest_path}")
        
    except Exception as e:
        print(f"Failed to process {src_name}: {e}")

print("Done.")

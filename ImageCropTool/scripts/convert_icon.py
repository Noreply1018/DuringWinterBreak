from PIL import Image
import os

def convert_to_ico(input_path, output_path):
    try:
        img = Image.open(input_path)
        img.save(output_path, format='ICO', sizes=[(256, 256)])
        print(f"Successfully converted {input_path} to {output_path}")
    except Exception as e:
        print(f"Error converting {input_path} to {output_path}: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "1.png")
    output_file = os.path.join(current_dir, "icon.ico")
    
    if os.path.exists(input_file):
        convert_to_ico(input_file, output_file)
    else:
        print(f"Input file not found: {input_file}")

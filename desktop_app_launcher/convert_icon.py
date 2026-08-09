import sys
from PIL import Image

def convert():
    img_path = sys.argv[1]
    ico_path = sys.argv[2]
    img = Image.open(img_path)
    # Ensure it's square
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
    img.save(ico_path, format="ICO", sizes=[(256, 256)])
    print(f"Converted {img_path} to {ico_path}")

if __name__ == "__main__":
    convert()

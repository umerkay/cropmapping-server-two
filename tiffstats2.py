from PIL import Image, TiffImagePlugin
import tifffile

def print_pil_metadata(filepath):
    print("== PIL Metadata ==")
    with Image.open(filepath) as img:
        print(f"Format: {img.format}")
        print(f"Size: {img.size}")
        print(f"Mode: {img.mode}")
        
        # Print TIFF tags
        if hasattr(img, "tag_v2"):
            for tag, value in img.tag_v2.items():
                print(f"Tag {tag}: {value}")
        else:
            print("No tag_v2 metadata found.")

def print_tifffile_metadata(filepath):
    print("\n== tifffile Metadata ==")
    with tifffile.TiffFile(filepath) as tif:
        for page_index, page in enumerate(tif.pages):
            print(f"\n-- Page {page_index} --")
            for tag in page.tags.values():
                name, value = tag.name, tag.value
                print(f"{name}: {value}")

if __name__ == "__main__":
    filepath = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/mapdata/Punjab2024First/stitched_tile_T43RDM.tiff"  # 🔁 Replace with your TIFF file path
    print_pil_metadata(filepath)
    print_tifffile_metadata(filepath)

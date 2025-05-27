import torch
import os
import tifffile
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from skimage import exposure
from api.model.model import UNet  # Assuming your UNet model is imported from a file
from api.model.dataloader import CropDataset  # If needed, otherwise you can customize loading here

def createMasks(input_patches=None, profile=None, return_memory_masks=True):
    # Define the color mapping for each class
    CLASS_COLORS = {
        0: (0, 0, 0),            # Black
        1: (255, 192, 203),       # Pink - Natural
        2: (144, 238, 144),       # Light Green - Forest
        3: (255, 255, 0),         # Yellow - Corn
        4: (0, 100, 0),           # Dark Green - Soybeans
        5: (102, 205, 170),       # Medium Aquamarine - Wetlands
        6: (128, 128, 128),       # Gray - Developed/Barren
        7: (70, 130, 180),        # Steel Blue - Open Water
        8: (139, 69, 19),         # Saddle Brown - Wheat
        9: (255, 192, 203),       # Light Pink - Alfalfa
        10: (189, 183, 107),      # Dark Khaki - Fallow/Idle
        11: (255, 0, 0),          # Red - Cotton
        12: (255, 165, 0),        # Orange - Sorghum
        13: (0, 206, 209),        # Dark Turquoise - Other
    }

    # Function to convert prediction mask to RGB image using class colors
    def convert_mask_to_rgb(pred_mask):
        height, width = pred_mask.shape
        rgb_mask = np.zeros((height, width, 3), dtype=np.uint8)
        
        for class_id, color in CLASS_COLORS.items():
            rgb_mask[pred_mask == class_id] = color

        return rgb_mask

    # Load the model and checkpoint
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet(in_channels=18, out_channels=14).to(device)
    checkpoint_path = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/api/model/unet_best.pth"
    model.load_state_dict(torch.load(checkpoint_path))
    model.to(device)
    print(f"Model loaded from {checkpoint_path}")

    save_dir = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/patches_masks"
    os.makedirs(save_dir, exist_ok=True)  # Create the save directory if it doesn't exist
    
    # Arrays to store masks if we're returning them in memory
    rgb_masks = []
    class_masks = []
    
    if input_patches is not None:
        # Process patches directly from memory
        # Iterate through each patch
        for i in range(input_patches.shape[0]):
            # Get the current patch
            image = input_patches[i].astype(np.float32) / 255.0
            
            # Convert to PyTorch tensor and move to device
            image_tensor = torch.tensor(image).unsqueeze(0).to(device)  # (1, C, H, W)
            
            # Pass the image through the model
            model.eval()
            with torch.no_grad():
                prediction = model(image_tensor)
                pred_mask = torch.argmax(prediction, dim=1).squeeze(0).cpu().numpy()  # (H, W)
            
            # Convert the predicted mask to RGB using the class colors
            rgb_mask = convert_mask_to_rgb(pred_mask)
            
            if return_memory_masks:
                # Store masks in memory
                rgb_masks.append(rgb_mask)
                class_masks.append(pred_mask)
            
            # Still save to disk for compatibility with existing code
            save_path = os.path.join(save_dir, f"patch_{i}_mask.png")
            Image.fromarray(rgb_mask).save(save_path)
            
            raw_tiff_save_path = os.path.join(save_dir, f"patch_{i}_class.tif")
            tifffile.imwrite(raw_tiff_save_path, pred_mask.astype(np.uint8))
    else:
        # Function to load image and make prediction
        def process_and_save(model, image_path, save_dir, device):
            # Load the image
            image = tifffile.imread(image_path).astype(np.float32) / 255.0
            
            # Convert to PyTorch tensor and move to device
            image_tensor = torch.tensor(image).unsqueeze(0).to(device)  # (1, C, H, W)

            # Pass the image through the model
            model.eval()
            with torch.no_grad():
                prediction = model(image_tensor)
                pred_mask = torch.argmax(prediction, dim=1).squeeze(0).cpu().numpy()  # (H, W)

            # Convert the predicted mask to RGB using the class colors
            rgb_mask = convert_mask_to_rgb(pred_mask)

            # Save the RGB mask as a PNG
            chip_id = os.path.basename(image_path).replace('_merged.tif', '')
            save_path = os.path.join(save_dir, f"{chip_id}_mask.png")
            Image.fromarray(rgb_mask).save(save_path)
            
            # Save the raw class predictions as a TIFF
            raw_tiff_save_path = os.path.join(save_dir, f"{chip_id}_class.tif")
            tifffile.imwrite(raw_tiff_save_path, pred_mask.astype(np.uint8))
            
            return rgb_mask, pred_mask

        # Process all files in input_dir
        input_dir = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/patches"
        for i, filename in enumerate(sorted(os.listdir(input_dir))):
            if filename.endswith('.tif'):
                image_path = os.path.join(input_dir, filename)
                rgb_mask, class_mask = process_and_save(model, image_path, save_dir, device)
                
                if return_memory_masks:
                    rgb_masks.append(rgb_mask)
                    class_masks.append(class_mask)
    
    if return_memory_masks:
        return save_dir, rgb_masks, class_masks
    else:
        return save_dir

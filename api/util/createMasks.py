import torch
import os
import tifffile
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from skimage import exposure
from api.model.model import UNet  # Assuming your UNet model is imported from a file
from api.model.dataloader import CropDataset  # If needed, otherwise you can customize loading here

def createMasks():
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

    # Function to load image and make prediction
    def process_and_save(model, image_path, save_dir, device):
        # Load the image
        image = tifffile.imread(image_path).astype(np.float32) / 255.0

        # Ensure the image has the correct shape
        # if image.shape[2] != 18:
            # raise ValueError(f"Unexpected image shape: {image.shape}")
        
        # Convert to PyTorch tensor and move to device
        image_tensor = torch.tensor(image).unsqueeze(0).to(device)  # (1, C, H, W)

        # Pass the image through the model
        model.eval()
        with torch.no_grad():
            # print(image_tensor.shape)
            prediction = model(image_tensor)
            pred_mask = torch.argmax(prediction, dim=1).squeeze(0).cpu().numpy()  # (H, W)

        # Convert the predicted mask to RGB using the class colors
        rgb_mask = convert_mask_to_rgb(pred_mask)

        # Save the RGB mask as a PNG
        chip_id = os.path.basename(image_path).replace('_merged.tif', '')
        save_path = os.path.join(save_dir, f"{chip_id}_mask.png")
        Image.fromarray(rgb_mask).save(save_path)
        # print(f"Saved mask to {save_path}")

    # Main function to process all images in a directory
    def process_directory(model, input_dir, save_dir, device):
        os.makedirs(save_dir, exist_ok=True)  # Create the save directory if it doesn't exist
        for filename in os.listdir(input_dir):
            if filename.endswith('.tif'):
                image_path = os.path.join(input_dir, filename)
                process_and_save(model, image_path, save_dir, device)

    # Load the model and checkpoint
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet(in_channels=18, out_channels=14).to(device)
    checkpoint_path = "/home/vision-16/CropTypeMap/Portal/server/api/model/unet_best.pth"  # Adjust as needed
    model.load_state_dict(torch.load(checkpoint_path))
    model.to(device)
    print(f"Model loaded from {checkpoint_path}")

    # Define the input directory and save directory
    input_dir = "tempData/patches"
    save_dir = "tempData/patches_masks"

    # Process all files and save the masks
    process_directory(model, input_dir, save_dir, device)
    
    return save_dir

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import tifffile  # Use tifffile for reading TIFF files with multiple channels
from PIL import Image

class CropDataset(Dataset):
    def __init__(self, dataset, data_dir, transform=None):
        self.dataset = dataset
        self.data_dir = data_dir
        self.transform = transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        chip_id = self.dataset[idx]
        image_path = f"{self.data_dir}/{chip_id}_merged.tif"
        mask_path = f"{self.data_dir}/{chip_id}.mask.tif"

        # Load image and mask
        image = tifffile.imread(image_path)
        mask = np.array(Image.open(mask_path))

        # Ensure image and mask have the expected shapes
        if image.ndim == 3 and image.shape[2] == 18:
            # print(f"Image shape: {image.shape}")  # Should be (height, width, 18)
            pass
        else:
            raise ValueError(f"Unexpected image shape: {image.shape}")

        # Normalize the image
        image = image.astype(np.float32) / 255.0

        # Convert numpy arrays to PyTorch tensors
        image_tensor = torch.tensor(image).permute(2, 0, 1)  # (C, H, W)
        mask_tensor = torch.tensor(mask, dtype=torch.long) - 1   # (H, W)

        if self.transform:
            augmented = self.transform(image=image_tensor.numpy(), mask=mask_tensor.numpy())
            image_tensor = torch.tensor(augmented['image'])
            mask_tensor = torch.tensor(augmented['mask'], dtype=torch.long)

        return image_tensor, mask_tensor

# Load the dataset
# from datasets import load_dataset
# ds = load_dataset("ibm-nasa-geospatial/multi-temporal-crop-classification")

def readFiles():
    file_path = '/home/vision-16/CropTypeMap/PrithviData/data/training_data.txt'
    train_lines = []
    with open(file_path, 'r') as file:
        for line in file:
            train_lines.append(line.strip())
    
    file_path = '/home/vision-16/CropTypeMap/PrithviData/data/validation_data.txt'
    val_lines = []
    with open(file_path, 'r') as file:
        for line in file:
            val_lines.append(line.strip())
            
    return [train_lines, val_lines]


def getDataLoaders(path = "/home/vision-16/CropTypeMap/PrithviData/data"):
    # Define paths to training and validation data directories
    train_data_dir = f"{path}/training_chips"
    val_data_dir = f"{path}/validation_chips"
    
    [train_ds, val_ds] = readFiles()

    # Create training and validation datasets
    train_dataset = CropDataset(train_ds, data_dir=train_data_dir)
    val_dataset = CropDataset(val_ds, data_dir=val_data_dir)

    # Create DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=4)
    
    return [train_loader, val_loader]
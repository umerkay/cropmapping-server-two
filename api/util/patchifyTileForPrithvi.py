import os
import rasterio
import numpy as np

def patchifyTile(tiff_files, output_folder = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/patches", save_to_disk=True):
    patch_size = 224

    def create_patches(tiff_files):
        all_patches = []
        
        # Read each band and create patches
        for file in tiff_files:
            patches = []
            with rasterio.open(file) as src:
                img = src.read(1)  # Read the first band
                profile = src.profile  # Get the profile for metadata
                
                # Create patches
                # Get dimensions of the image
                height, width = img.shape
                
                count = 0
                # Create patches of size patch_size x patch_size
                for i in range(0, height - patch_size + 1, patch_size):
                    for j in range(0, width - patch_size + 1, patch_size):
                        patch = img[i:i + patch_size, j:j + patch_size]
                        count += 1
                        patches.append(patch)

                all_patches.append(patches)
        
        # Iterate through each list of arrays
        all_data = []
        for data_list in all_patches:
            # Convert the list of arrays to a NumPy array and append to all_data
            all_data.append(np.array(data_list))

        # Stack the arrays along a new axis to get the desired shape
        result = np.stack(all_data, axis=-1)  # This will give you shape (256, 224, 224, 18)
        print(result.shape)
        reshaped_result = np.transpose(result, (0, 3, 1, 2))
        return reshaped_result, profile

    def save_patches(patches, profile, output_folder):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Save each patch as a separate TIFF file
        for i in range(patches.shape[0]):
            patch = patches[i, :, :, :]  # Select the ith patch
            patch_filename = os.path.join(output_folder, f"patch_{i}.tif")
            
            # Update the profile for saving
            new_profile = profile.copy()
            new_profile.update({
                'height': patch.shape[1],
                'width': patch.shape[2],
                'count': patch.shape[0],
                'transform': profile['transform']  # Retain original transform
            })
            
            with rasterio.open(patch_filename, 'w', **new_profile) as dst:
                dst.write(patch)

    patches, profile = create_patches(tiff_files)
    print(patches.shape)
    
    if save_to_disk:
        save_patches(patches, profile, output_folder)
        return output_folder, len(patches), patches.shape
    else:
        # Return patches directly for in-memory processing
        return patches, profile
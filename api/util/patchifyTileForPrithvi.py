import os
import rasterio
import numpy as np

def patchifyTile(tiff_files, output_folder = "tempData/patches"):
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
                print(img.shape)
                # patches = patchify(img, (224, 224), step=224) 
                # Get dimensions of the image
                height, width = img.shape
                
                count = 0
                # Create patches of size patch_size x patch_size
                for i in range(0, height - patch_size + 1, patch_size):
                    for j in range(0, width - patch_size + 1, patch_size):
                        patch = img[i:i + patch_size, j:j + patch_size]
                        count += 1
                        patches.append(patch)

                print("From single file:", len(patches))
                print("Each patch of size:", patches[-1].shape)
                all_patches.append(patches)
                # print(patches[0].shape)
                # Reshape and stack patches along the new dimension
                # stacked_patches.append(patches)
        
        # Concatenate patches along the channel dimension
        # stacked_patches = np.concatenate(all_patches, axis=-1)
        # Stack patches along the channel dimension
        # Iterate through each list of arrays
        all_data = []
        for data_list in all_patches:
            # Convert the list of arrays to a NumPy array and append to all_data
            all_data.append(np.array(data_list))

        # Now all_data is a list of NumPy arrays where each array has the shape (256, 224, 224)

        # Stack the arrays along a new axis to get the desired shape
        result = np.stack(all_data, axis=-1)  # This will give you shape (256, 224, 224, 18)
        print(result.shape)
        reshaped_result = np.transpose(result, (0, 3, 1, 2))
        # stacked_patches = np.stack(all_patches, axis=-1)
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
    save_patches(patches, profile, output_folder)

    return output_folder, len(patches), patches.shape
import earthaccess

# Define variables before using them
short_name = 'HLSS30'
cloud_hosted = True
bounding_box = [
    29.726055483658396,  # min latitude
    71.06736346307093,   # min longitude
    30.692783115760562,  # max latitude
    72.23356253864947    # max longitude
]
temporal_range = ("2023-04-01", "2023-12-01")
cloud_cover = (0, 30)

# Login to Earth Data
auth = earthaccess.login(strategy="netrc")

# Search for data
results = earthaccess.search_data(
    short_name=short_name,
    cloud_hosted=cloud_hosted,  # Prefer cloud-hosted data for easy access
    temporal=temporal_range,  # Specify the date range of interest
    bounding_box=(
        bounding_box[0],  # lower_left_lat
        bounding_box[1],  # lower_left_lon
        bounding_box[2],  # upper_right_lat
        bounding_box[3]   # upper_right_lon
    ),  # Use the bounding box filter
    cloud_cover=cloud_cover,  # Filter for images with less than 30% cloud cover
)

# Print results information
print(f"Found {len(results)} results")

# Filter results for T36WVD
filtered_results = []
for result in results:
    for file_url in result.data_links():
        if "T36WVD" in file_url:
            filtered_results.append(result)
            break  # Found a match, no need to check other links

# Print filtered results
print(f"Found {len(filtered_results)} results with T36WVD")
if filtered_results:
    print("\nFirst filtered result:")
    print(filtered_results[0])
    # print("\nData links for first filtered result:")
    # for link in filtered_results[0].data_links():
    #     print(f"- {link}")
    
    # Print first data link for each filtered result
    print("\nFirst data link for each filtered result:")
    for i, result in enumerate(filtered_results):
        data_links = result.data_links()
        if data_links:
            print(f"Result {i+1}: {data_links[0]}")
        else:
            print(f"Result {i+1}: No data links available")
else:
    print("No results containing T36WVD found.")
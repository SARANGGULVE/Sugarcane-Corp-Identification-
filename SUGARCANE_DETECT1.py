import numpy as np
import pandas as pd
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import geopandas as gpd

def detect_sugarcane(satellite_image_path, bands_excel_path):
    # Read satellite imagery
    with rasterio.open(satellite_image_path) as src:
        # Read all bands
        image = src.read()
        # Get metadata
        meta = src.meta
        transform = src.transform
        
    # Read bands wavelength information from Excel
    bands_info = pd.read_excel(bands_excel_path)
    
    # Normalize image data
    scaler = StandardScaler()
    normalized_image = np.zeros_like(image, dtype=np.float32)
    for i in range(image.shape[0]):
        normalized_image[i] = scaler.fit_transform(image[i].reshape(-1, 1)).reshape(image[i].shape)
    
    # Calculate NDVI (Normalized Difference Vegetation Index)
    nir_band = normalized_image[3]  # Assuming NIR is band 4
    red_band = normalized_image[2]  # Assuming Red is band 3
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    
    # Define sugarcane threshold (adjust these values based on your specific case)
    ndvi_threshold = 0.6
    
    # Create sugarcane mask
    sugarcane_mask = ndvi > ndvi_threshold
    
    # Get coordinates of detected sugarcane plots
    rows, cols = np.where(sugarcane_mask)
    coords = []
    for row, col in zip(rows, cols):
        x, y = rasterio.transform.xy(transform, row, col)
        coords.append((x, y))
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    
    # Plot the detected sugarcane areas
    plt.imshow(sugarcane_mask, cmap='RdYlGn')
    plt.colorbar(label='Sugarcane Presence')
    plt.title('Detected Sugarcane Plots')
    
    # Print coordinates of detected plots
    print("\nSugarcane Plot Coordinates (Longitude, Latitude):")
    for lon, lat in coords[:10]:  # Show first 10 coordinates
        print(f"Longitude: {lon:.6f}, Latitude: {lat:.6f}")
    
    plt.show()
    
    return sugarcane_mask, coords

# Example usage
satellite_image_path = "path_to_your_satellite_image.tif"
bands_excel_path = "path_to_your_bands_info.xlsx"

# Run detection
mask, coordinates = detect_sugarcane(satellite_image_path, bands_excel_path)

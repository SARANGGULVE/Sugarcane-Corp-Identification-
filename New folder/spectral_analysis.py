import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from xml.dom import minidom
import rasterio
import geopandas as gpd
import os
from shapely.geometry import Point, Polygon

def read_kml(kml_file):
    """
    Read coordinates from KML file.
    
    Args:
        kml_file: Path to the KML file
    
    Returns:
        List of coordinates as [longitude, latitude] pairs
    """
    try:
        print(f"\nReading coordinates from {kml_file}...")
        # Read KML file using geopandas
        gdf = gpd.read_file(kml_file, driver='KML')
        
        # Extract coordinates from geometries
        coordinates = []
        for geom in gdf.geometry:
            if isinstance(geom, Point):
                coordinates.append([geom.x, geom.y])
            elif isinstance(geom, Polygon):
                # For polygons, use the centroid
                centroid = geom.centroid
                coordinates.append([centroid.x, centroid.y])
        
        print(f"Found {len(coordinates)} coordinate pairs")
        return coordinates
    except Exception as e:
        print(f"Error reading KML file: {e}")
        return None

def get_spectral_profile_from_local(roi_point, band_files):
    """
    Get spectral profile from local band files.
    
    Args:
        roi_point: [longitude, latitude] coordinates
        band_files: Dictionary mapping band names to file paths
        
    Returns:
        wavelengths: List of wavelengths
        reflectance: List of reflectance values
    """
    # Define band wavelengths (in nanometers)
    band_wavelengths = {
        'B2': 490,    # Blue
        'B3': 560,    # Green
        'B4': 665,    # Red
        'B5': 705,    # Red Edge 1
        'B6': 740,    # Red Edge 2
        'B7': 783,    # Red Edge 3
        'B8': 842,    # NIR
        'B8A': 865,   # NIR (narrow)
        'B9': 945,    # Water Vapour
        'B11': 1615,  # SWIR 1
        'B12': 2190   # SWIR 2
    }
    
    reflectance = []
    wavelengths = []
    
    # Process each band file
    for band_name, wavelength in band_wavelengths.items():
        if band_name in band_files:
            try:
                with rasterio.open(band_files[band_name]) as src:
                    # Convert geographic coordinates to pixel coordinates
                    py, px = src.index(roi_point[0], roi_point[1])
                    
                    # Read pixel value
                    window = ((py-1, py+2), (px-1, px+2))  # 3x3 window around point
                    data = src.read(1, window=window)
                    
                    # Calculate mean value (excluding nodata)
                    nodata = src.nodata if src.nodata is not None else 0
                    valid_data = data[data != nodata]
                    if len(valid_data) > 0:
                        mean_value = np.mean(valid_data)
                        reflectance.append(mean_value)
                        wavelengths.append(wavelength)
                    else:
                        print(f"No valid data found for band {band_name} at the specified location")
            except Exception as e:
                print(f"Error processing band {band_name}: {e}")
    
    return wavelengths, reflectance

def plot_spectral_profile(wavelengths, reflectance, title='Reflectance vs Wavelength (Sentinel-2)'):
    """
    Plot spectral profile using matplotlib.
    
    Args:
        wavelengths: List of wavelengths
        reflectance: List of reflectance values
        title: Plot title
    """
    plt.figure(figsize=(10, 6))
    plt.plot(wavelengths, reflectance, 'o-', linewidth=2, markersize=5)
    plt.title(title)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Reflectance')
    plt.grid(True)
    plt.show()

def main():
    # Specify the path to your KML file
    kml_file = 'your_roi.kml'  # Replace with your KML file path
    
    # Specify the directory containing your band images
    band_dir = 'band_images'  # Replace with your band images directory
    
    # Create a dictionary mapping band names to file paths
    band_files = {}
    for band in ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11', 'B12']:
        # Look for files containing the band name
        potential_files = [f for f in os.listdir(band_dir) if band in f]
        if potential_files:
            band_files[band] = os.path.join(band_dir, potential_files[0])
    
    # Read coordinates from KML file
    coordinates = read_kml(kml_file)
    
    if coordinates is None:
        print("Could not read coordinates from KML file. Using default coordinates.")
        coordinates = [[74.5, 19.5]]  # Default coordinates
    
    # Create a list to store spectral profiles
    all_profiles = []
    
    # Get spectral profile for each coordinate
    for i, coord in enumerate(coordinates):
        print(f"\nProcessing location {i+1}: {coord}")
        wavelengths, reflectance = get_spectral_profile_from_local(coord, band_files)
        
        if wavelengths and reflectance:
            all_profiles.append(reflectance)
            # Plot individual profile
            plot_spectral_profile(wavelengths, reflectance, 
                                title=f'Sugarcane Spectral Profile - Location {i+1}')
    
    # Calculate and plot average profile
    if len(all_profiles) > 1:
        print("\nCalculating average spectral profile...")
        # Make sure all profiles have the same number of bands
        min_length = min(len(profile) for profile in all_profiles)
        all_profiles = [profile[:min_length] for profile in all_profiles]
        wavelengths = wavelengths[:min_length]
        
        avg_reflectance = np.mean(all_profiles, axis=0)
        plot_spectral_profile(wavelengths, avg_reflectance, 
                            title='Average Sugarcane Spectral Profile')

if __name__ == "__main__":
    main() 
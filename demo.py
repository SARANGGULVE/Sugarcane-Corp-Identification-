import ee
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Initialize Earth Engine
try:
    auth_choice = input("Do you want to authenticate Earth Engine? (yes/no): ").lower()
    if auth_choice == 'yes':
        ee.Authenticate()
    ee.Initialize()
except Exception as e:
    print("Please authenticate Earth Engine first using: ee.Authenticate()")
    print("Then run: ee.Initialize()")
    raise e

def load_roi_from_kml(kml_path):
    """
    Load Region of Interest from KML file
    """
    roi = gpd.read_file(kml_path)
    # Convert to GEE geometry
    roi_ee = ee.Geometry.Polygon(roi.geometry.iloc[0].exterior.coords.xy)
    return roi_ee

def get_sentinel2_collection(roi, start_date, end_date, cloud_threshold=20):
    """
    Get filtered Sentinel-2 collection
    """
    collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                 .filterBounds(roi)
                 .filterDate(start_date, end_date)
                 .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_threshold)))
    return collection

def calculate_indices(image):
    """
    Calculate vegetation indices (NDVI, EVI, NDWI)
    """
    # Get bands
    nir = image.select('B8')
    red = image.select('B4')
    green = image.select('B3')
    blue = image.select('B2')
    swir = image.select('B11')

    # Calculate NDVI
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    
    # Calculate EVI
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {
            'NIR': nir,
            'RED': red,
            'BLUE': blue
        }
    ).rename('EVI')
    
    # Calculate NDWI
    ndwi = image.normalizedDifference(['B3', 'B11']).rename('NDWI')
    
    return image.addBands([ndvi, evi, ndwi])

def detect_sugarcane(image):
    """
    Detect sugarcane using NDVI threshold
    """
    # Create binary mask for sugarcane (NDVI > 0.5)
    sugarcane_mask = image.select('NDVI').gt(0.5).rename('sugarcane')
    return image.addBands(sugarcane_mask)

def extract_coordinates(image, roi):
    """
    Extract coordinates of sugarcane pixels
    """
    # Get sugarcane pixels
    sugarcane = image.select('sugarcane')
    
    # Convert to points
    points = sugarcane.updateMask(sugarcane).reduceToVectors({
        'geometry': roi,
        'scale': 10,
        'geometryType': 'Point'
    })
    
    return points

def save_to_excel(points, output_file):
    """
    Save coordinates to Excel file
    """
    # Convert to pandas DataFrame
    df = pd.DataFrame(points.getInfo()['features'])
    df['coordinates'] = df['geometry'].apply(lambda x: x['coordinates'])
    df['latitude'] = df['coordinates'].apply(lambda x: x[1])
    df['longitude'] = df['coordinates'].apply(lambda x: x[0])
    
    # Save to Excel
    df[['latitude', 'longitude']].to_excel(output_file, index=False)
    print(f"Coordinates saved to {output_file}")

def visualize_results(image, roi, output_file):
    """
    Visualize results on a map
    """
    # Create visualization parameters
    vis_params = {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000
    }
    
    # Create the map
    map_center = roi.centroid().getInfo()['coordinates']
    map_vis = ee.Image(image).visualize(vis_params)
    
    # Add sugarcane mask
    sugarcane_vis = ee.Image(image).select('sugarcane').visualize({
        'palette': ['red'],
        'min': 0,
        'max': 1
    })
    
    # Create the map
    map_obj = ee.Map()
    map_obj.setCenter(map_center[0], map_center[1], 10)
    map_obj.addLayer(map_vis, {}, 'Sentinel-2')
    map_obj.addLayer(sugarcane_vis, {}, 'Sugarcane')
    
    # Save the map
    map_obj.save(output_file)
    print(f"Map saved to {output_file}")

def main():
    # Parameters
    kml_path = 'roi.kml'  # Replace with your KML file path
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    cloud_threshold = 20
    output_excel = 'sugarcane_coordinates.xlsx'
    output_map = 'sugarcane_map.html'

    # Load ROI
    roi = load_roi_from_kml(kml_path)
    
    # Get Sentinel-2 collection
    collection = get_sentinel2_collection(roi, start_date, end_date, cloud_threshold)
    
    # Get the most recent image
    image = collection.sort('system:time_start', False).first()
    
    # Calculate indices
    image_with_indices = calculate_indices(image)
    
    # Detect sugarcane
    image_with_sugarcane = detect_sugarcane(image_with_indices)
    
    # Extract coordinates
    points = extract_coordinates(image_with_sugarcane, roi)
    
    # Save results
    save_to_excel(points, output_excel)
    visualize_results(image_with_sugarcane, roi, output_map)

if __name__ == "__main__":
    main()
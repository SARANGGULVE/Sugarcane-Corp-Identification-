# Sugarcane Detection using Google Earth Engine

This Python script uses Google Earth Engine (GEE) to detect sugarcane crops using Sentinel-2 satellite imagery. It processes satellite data to identify sugarcane fields based on vegetation indices and exports the coordinates of detected sugarcane pixels.

## Prerequisites

1. Python 3.7 or higher
2. Google Earth Engine account
3. Required Python packages (listed in requirements.txt)

## Setup

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Authenticate with Google Earth Engine:
```python
import ee
ee.Authenticate()
ee.Initialize()
```

3. Prepare your KML file:
   - Create a KML file defining your Region of Interest (ROI)
   - Place the KML file in the same directory as the script
   - Update the `kml_path` variable in the script with your KML filename

## Usage

1. Run the script:
```bash
python sugarcane_detection.py
```

2. The script will:
   - Load your ROI from the KML file
   - Fetch Sentinel-2 imagery for the specified date range
   - Calculate vegetation indices (NDVI, EVI, NDWI)
   - Detect sugarcane using NDVI threshold (> 0.5)
   - Extract coordinates of detected sugarcane pixels
   - Save coordinates to an Excel file
   - Generate an interactive map visualization

## Output

The script generates two output files:
1. `sugarcane_coordinates.xlsx`: Contains latitude and longitude coordinates of detected sugarcane pixels
2. `sugarcane_map.html`: Interactive map showing the Sentinel-2 imagery with highlighted sugarcane regions

## Customization

You can modify the following parameters in the `main()` function:
- `start_date` and `end_date`: Date range for satellite imagery
- `cloud_threshold`: Maximum allowed cloud coverage percentage
- `output_excel`: Name of the output Excel file
- `output_map`: Name of the output map file

## Notes

- The script uses NDVI > 0.5 as the threshold for sugarcane detection. This threshold may need adjustment based on your specific region and conditions.
- Make sure you have sufficient permissions and quota in your Google Earth Engine account.
- The script processes the most recent available image within the specified date range. 
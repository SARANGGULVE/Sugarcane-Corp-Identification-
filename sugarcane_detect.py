import ee
import folium
import matplotlib.pyplot as plt

# Initialize the Earth Engine module
ee.Authenticate()
ee.Initialize()

# Define the region of interest (ROI)
roi = ee.Geometry.Polygon(
    [[-122.0, 37.0], [-122.0, 38.0], [-121.0, 38.0], [-121.0, 37.0]]
)

# Load Sentinel-2 surface reflectance data
sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(roi) \
    .filterDate('2022-09-01', '2023-04-30') \
    .select(['B2', 'B3', 'B4', 'B8', 'B11'])

# Define a function to calculate NDVI
def calculate_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4'])
    return image.addBands(ndvi.rename('NDVI'))

# Map the function over the image collection
sentinel2_with_ndvi = sentinel2.map(calculate_ndvi)

# Reduce the image collection to get the mean reflectance
mean_reflectance = sentinel2_with_ndvi.mean()

# Extract reflectance values for each band
bands = [
    {'band': 'B2', 'wavelength': 490},    # Blue
    {'band': 'B3', 'wavelength': 560},    # Green
    {'band': 'B4', 'wavelength': 665},    # Red
    {'band': 'B8', 'wavelength': 842},    # NIR
    {'band': 'B11', 'wavelength': 1615}   # SWIR 1
]

reflectance = [mean_reflectance.select(band['band']).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=roi,
    scale=10
).get(band['band']) for band in bands]

# Create an array of reflectance values to match with the corresponding wavelengths
wavelengths = [band['wavelength'] for band in bands]

# Plot reflectance vs wavelength
plt.plot(wavelengths, reflectance)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Reflectance')
plt.title('Reflectance vs Wavelength (Sentinel-2)')
plt.show()

# Define a classification algorithm
classifier = ee.Classifier.randomForest(10)

# Train the classifier
training_data = ee.FeatureCollection(  # Replace with your training data
    'users/username/dataset'
).filterBounds(roi)

trained_classifier = classifier.train(
    features=training_data,
    classProperty='landcover',
    inputProperties=['B2', 'B3', 'B4', 'B8', 'B11', 'NDVI']
)

# Classify the images
classified_images = sentinel2_with_ndvi.classify(trained_classifier)

# Create a sugarcane detection map
sugarcane_map = classified_images.eq(1)

# Visualize the sugarcane detection map
map = folium.Map(location=[37.5, -122.0], zoom_start=10)
folium.TileLayer('Stamen Terrain').add_to(map)
folium.GeoJson(sugarcane_map.getDownloadURL(), name='Sugarcane Detection').add_to(map)
map.save('sugarcane_detection_map.html')

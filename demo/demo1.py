import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd
from shapely.geometry import mapping
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpectralProcessor:
    """Handles spectral data processing and index calculations."""
    
    def __init__(self):
        self.indices = {
            'NDVI': self.calculate_ndvi,
            'EVI': self.calculate_evi,
            'GNDVI': self.calculate_gndvi
        }
    
    @staticmethod
    def calculate_ndvi(nir_band, red_band):
        """Calculate NDVI from NIR and RED bands."""
        return (nir_band - red_band) / (nir_band + red_band + 1e-8)
    
    @staticmethod
    def calculate_evi(nir_band, red_band, blue_band):
        """Calculate EVI using NIR, RED, and BLUE bands."""
        return 2.5 * ((nir_band - red_band) / 
                      (nir_band + 6 * red_band - 7.5 * blue_band + 1))
    
    @staticmethod
    def calculate_gndvi(nir_band, green_band):
        """Calculate Green NDVI."""
        return (nir_band - green_band) / (nir_band + green_band + 1e-8)

class SugarcaneDetector:
    """Main class for sugarcane detection workflow."""
    
    def __init__(self, spectral_ref_path, image_path, roi_path):
        """
        Initialize detector with file paths.
        
        Args:
            spectral_ref_path (str): Path to spectral reference Excel file
            image_path (str): Path to satellite image GeoTIFF
            roi_path (str): Path to ROI KML file
        """
        self.spectral_ref_path = Path(spectral_ref_path)
        self.image_path = Path(image_path)
        self.roi_path = Path(roi_path)
        self.spectral_processor = SpectralProcessor()
        self.validate_inputs()
        
    def validate_inputs(self):
        """Validate input file existence and formats."""
        for path in [self.spectral_ref_path, self.image_path, self.roi_path]:
            if not path.exists():
                raise FileNotFoundError(f"Input file not found: {path}")
    
    def load_spectral_reference(self):
        """Load and process spectral reference data."""
        try:
            df = pd.read_excel(self.spectral_ref_path)
            required_columns = ['Wavelength', 'Reflectance']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("Missing required columns in spectral reference file")
            return df
        except Exception as e:
            logger.error(f"Error loading spectral reference: {e}")
            raise
    
    def load_and_clip_image(self):
        """Load satellite image and clip to ROI."""
        try:
            with rasterio.open(self.image_path) as src:
                # Read ROI
                roi_gdf = gpd.read_file(self.roi_path)
                roi_gdf = roi_gdf.to_crs(src.crs)
                
                # Clip image to ROI
                from rasterio.mask import mask
                roi_geometry = [mapping(geom) for geom in roi_gdf.geometry]
                clipped_image, clipped_transform = mask(src, roi_geometry, crop=True)
                
                return clipped_image, clipped_transform, src.meta
        except Exception as e:
            logger.error(f"Error loading and clipping image: {e}")
            raise

    def calculate_vegetation_indices(self, image_data):
        """Calculate vegetation indices from image bands."""
        try:
            # Assuming band order: NIR, Red, Green, Blue, SWIR
            nir_band = image_data[3]
            red_band = image_data[2]
            green_band = image_data[1]
            blue_band = image_data[0]
            
            indices = {
                'NDVI': self.spectral_processor.calculate_ndvi(nir_band, red_band),
                'EVI': self.spectral_processor.calculate_evi(nir_band, red_band, blue_band),
                'GNDVI': self.spectral_processor.calculate_gndvi(nir_band, green_band)
            }
            return indices
        except Exception as e:
            logger.error(f"Error calculating vegetation indices: {e}")
            raise

    def train_classifier(self, training_data, labels):
        """Train Random Forest classifier."""
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        scaler = StandardScaler()
        training_data_scaled = scaler.fit_transform(training_data)
        clf.fit(training_data_scaled, labels)
        return clf, scaler

    def detect_sugarcane(self):
        """Main detection workflow."""
        try:
            # Load reference data
            spectral_ref = self.load_spectral_reference()
            
            # Load and clip image
            image_data, transform, metadata = self.load_and_clip_image()
            
            # Calculate indices
            indices = self.calculate_vegetation_indices(image_data)
            
            # Prepare features for classification
            features = np.vstack([
                indices['NDVI'].ravel(),
                indices['EVI'].ravel(),
                indices['GNDVI'].ravel()
            ]).T
            
            # Train classifier (simplified for example)
            # In practice, you would need proper training data
            clf, scaler = self.train_classifier(features[:1000], np.random.binomial(1, 0.5, 1000))
            
            # Predict
            features_scaled = scaler.transform(features)
            predictions = clf.predict_proba(features_scaled)[:, 1]
            
            return self.generate_outputs(predictions, transform, metadata)
            
        except Exception as e:
            logger.error(f"Error in sugarcane detection: {e}")
            raise

    def generate_outputs(self, predictions, transform, metadata):
        """Generate output files."""
        try:
            # Reshape predictions to image dimensions
            prediction_map = predictions.reshape(metadata['height'], metadata['width'])
            
            # Generate CSV with coordinates and probabilities
            rows, cols = np.where(prediction_map > 0.5)
            lats, lons = rasterio.transform.xy(transform, rows, cols)
            
            results_df = pd.DataFrame({
                'Latitude': lats,
                'Longitude': lons,
                'Sugarcane_Probability': predictions[prediction_map.ravel() > 0.5]
            })
            
            # Save outputs
            results_df.to_csv('sugarcane_coordinates.csv', index=False)
            
            # Save classified image
            with rasterio.open(
                'classified_output.tif',
                'w',
                driver='GTiff',
                height=metadata['height'],
                width=metadata['width'],
                count=1,
                dtype=np.float32,
                crs=metadata['crs'],
                transform=transform
            ) as dst:
                dst.write(prediction_map.astype(np.float32), 1)
            
            # Generate KML
            gdf = gpd.GeoDataFrame(
                results_df,
                geometry=gpd.points_from_xy(results_df.Longitude, results_df.Latitude)
            )
            gdf.to_file('sugarcane_area.kml', driver='KML')
            
            return {
                'csv_path': 'sugarcane_coordinates.csv',
                'tiff_path': 'classified_output.tif',
                'kml_path': 'sugarcane_area.kml'
            }
            
        except Exception as e:
            logger.error(f"Error generating outputs: {e}")
            raise

def main():
    """Main execution function."""
    try:
        detector = SugarcaneDetector(
            spectral_ref_path='C:\\Users\\Sarang Gulve\\OneDrive\\Desktop\\Remote Sensing\\SUGARCANE_detection\\demo\\Sugarcane_Crop_Signature (1).xlsx' ,
            image_path='C:\\Users\\Sarang Gulve\\OneDrive\\Desktop\\Remote Sensing\\SUGARCANE_detection\\demo\\nashik\\B03_(Raw).tiff',
            roi_path=''
        )
        
        outputs = detector.detect_sugarcane()
        logger.info(f"Processing complete. Outputs generated: {outputs}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()

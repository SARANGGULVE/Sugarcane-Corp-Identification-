import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpectralAnalyzer:
    def __init__(self, excel_path, kml_path):
        """
        Initialize with paths to input files.
        
        Args:
            excel_path: Path to spectral signature Excel file
            kml_path: Path to KML file containing ROI
        """
        self.excel_path = Path(excel_path)
        self.kml_path = Path(kml_path)
        
        # Define Sentinel-2 bands and wavelengths
        self.bands = {
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

    def read_spectral_signature(self):
        """Read spectral signature data from Excel file."""
        try:
            logger.info(f"Reading spectral signature from {self.excel_path}")
            df = pd.read_excel(self.excel_path)
            return df
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise

    def read_roi(self):
        """Read ROI from KML file."""
        try:
            logger.info(f"Reading ROI from {self.kml_path}")
            gdf = gpd.read_file(self.kml_path, driver='KML')
            return gdf
        except Exception as e:
            logger.error(f"Error reading KML file: {e}")
            raise

    def plot_spectral_signature(self, wavelengths, reflectance, title='Reflectance vs Wavelength (Sentinel-2)'):
        """
        Plot spectral signature.
        
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

    def analyze(self):
        """Perform spectral analysis."""
        try:
            # Read spectral signature data
            spectral_data = self.read_spectral_signature()
            logger.info("Successfully read spectral signature data")

            # Read ROI
            roi = self.read_roi()
            logger.info(f"Successfully read ROI with {len(roi)} features")

            # Extract wavelengths and reflectance values
            wavelengths = list(self.bands.values())
            
            # Assuming your Excel file has columns matching the band names
            # Adjust this part based on your Excel file structure
            reflectance = []
            for band in self.bands.keys():
                if band in spectral_data.columns:
                    reflectance.append(spectral_data[band].mean())
                else:
                    logger.warning(f"Band {band} not found in Excel file")
                    reflectance.append(np.nan)

            # Plot the spectral signature
            self.plot_spectral_signature(
                wavelengths,
                reflectance,
                f'Sugarcane Spectral Signature - {self.kml_path.stem}'
            )

            return {
                'wavelengths': wavelengths,
                'reflectance': reflectance,
                'roi': roi
            }

        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            raise

def main():
    """Main execution function."""
    try:
        analyzer = SpectralAnalyzer(
            excel_path='Sugarcane Crop Signature.xlsx',
            kml_path='nashik, Gangavhare 1.kml'
        )
        
        results = analyzer.analyze()
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()

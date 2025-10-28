"""
Download Colorization Models
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Downloads the required model files for photo colorization.
"""

import os
import urllib.request
import logging

logger = logging.getLogger(__name__)

MODEL_URLS = {
    'colorization_deploy_v2.prototxt': 'https://raw.githubusercontent.com/richzhang/colorization/caffe/models/colorization_deploy_v2.prototxt',
    'colorization_release_v2.caffemodel': 'https://www.dropbox.com/s/dx0qvhhp5hbcx7z/colorization_release_v2.caffemodel?dl=1',
    'pts_in_hull.npy': 'https://raw.githubusercontent.com/richzhang/colorization/caffe/resources/pts_in_hull.npy'
}


def download_file(url, destination):
    """Download a file from URL to destination"""
    try:
        print(f"Downloading {os.path.basename(destination)}...")
        urllib.request.urlretrieve(url, destination)
        print(f"✓ Downloaded {os.path.basename(destination)}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {os.path.basename(destination)}: {e}")
        logger.error(f"Failed to download {destination}: {e}")
        return False


def download_colorization_models():
    """Download all required colorization model files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, 'models', 'colorization')
    
    # Create directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)
    
    print("\n=== Downloading Colorization Models ===\n")
    
    success_count = 0
    for filename, url in MODEL_URLS.items():
        filepath = os.path.join(models_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"✓ {filename} already exists")
            success_count += 1
            continue
        
        if download_file(url, filepath):
            success_count += 1
    
    print(f"\n=== Downloaded {success_count}/{len(MODEL_URLS)} files ===\n")
    
    if success_count == len(MODEL_URLS):
        print("✓ All colorization models ready!")
        return True
    else:
        print("⚠ Some models failed to download. Colorization will use basic method.")
        return False


if __name__ == "__main__":
    download_colorization_models()

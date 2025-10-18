#!/bin/bash
# Download Colorization Models for Railway Deployment
# This script downloads the required colorization model files automatically

echo "🎨 PhotoVault Release: Downloading colorization models..."

# Run the Python download script
python photovault/utils/download_models.py

# Check if download was successful
if [ $? -eq 0 ]; then
    echo "✅ PhotoVault Release: Colorization models downloaded successfully"
    
    # Verify all model files exist
    MODELS_DIR="photovault/utils/models/colorization"
    if [ -f "$MODELS_DIR/colorization_deploy_v2.prototxt" ] && \
       [ -f "$MODELS_DIR/colorization_release_v2.caffemodel" ] && \
       [ -f "$MODELS_DIR/pts_in_hull.npy" ]; then
        echo "✅ PhotoVault Release: All 3 colorization model files verified"
        
        # Show file sizes
        echo "📊 PhotoVault Release: Model file sizes:"
        ls -lh "$MODELS_DIR/" | grep -E "\.(prototxt|caffemodel|npy)$"
        
        exit 0
    else
        echo "⚠️ PhotoVault Release: Some model files are missing - colorization will use fallback method"
        exit 0  # Don't fail deployment
    fi
else
    echo "⚠️ PhotoVault Release: Model download failed - colorization will use fallback method"
    exit 0  # Don't fail deployment
fi

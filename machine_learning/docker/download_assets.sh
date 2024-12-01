#!/bin/bash
# download_assets.sh

# Exit on any error
set -e

echo "Starting download of assets from S3..."

# Download model and tokenizers
echo "Downloading model..."
aws s3 cp --recursive s3://alchemab-ml/autoantibody_model /app/autoantibody_model




# Download predict script
touch /app/predict.py
touch /app/utils.py
touch /app/aws_handler.py
wget -O /app/predict.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/predict.py
wget -O /app/analyse_metrics.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/analyse_metrics.py
wget -O /app/utils.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/utils.py
wget -O /app/aws_handler.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/aws_handler.py
wget -O /app/secrets_manager.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/secrets_manager.py

# Verify downloads
if [ ! -d "/app/autoantibody_model" ]; then
    echo "Error: model not downloaded"
    exit 1
fi
if [ ! -f "/app/predict.py" ]; then
    echo "Error: predict not downloaded"
    exit 1
fi
if [ ! -f "/app/utils.py" ]; then
    echo "Error: utils not downloaded"
    exit 1
fi
if [ ! -f "/app/aws_handler.py" ]; then
    echo "Error: aws handler not downloaded"
    exit 1
fi
if [ ! -f "/app/secrets_manager.py" ]; then
    echo "Error: aws secrets manager not downloaded"
    exit 1
fi

echo "All assets downloaded successfully"
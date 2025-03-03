aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 189545766043.dkr.ecr.eu-west-2.amazonaws.com

# Exit on any error
set -e

echo "Starting download of assets from S3..."

# Download model and tokenizers
echo "Downloading model..."
aws s3 cp --recursive s3://alchemab-ml/autoantibody_model temporary/autoantibody_model





# Download predict script
wget -O temporary/predict.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/predict_cpu.py
wget -O temporary/analyse_metrics.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/analyse_metrics.py
wget -O temporary/utils.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/utils.py
wget -O temporary/aws_handler.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/aws_handler.py
wget -O temporary/secrets_manager.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/secrets_manager.py
wget -O temporary/handler.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/autoantibody_app/api/functions/classify-small/handler.py

# Verify downloads
if [ ! -d "temporary/autoantibody_model" ]; then
    echo "Error: model not downloaded"
    exit 1
fi
if [ ! -f "temporary/predict.py" ]; then
    echo "Error: predict not downloaded"
    exit 1
fi
if [ ! -f "temporary/utils.py" ]; then
    echo "Error: utils not downloaded"
    exit 1
fi
if [ ! -f "temporary/aws_handler.py" ]; then
    echo "Error: aws handler not downloaded"
    exit 1
fi
if [ ! -f "temporary/secrets_manager.py" ]; then
    echo "Error: aws secrets manager not downloaded"
    exit 1
fi
if [ ! -f "temporary/handler.py" ]; then
    echo "Error: classify small handler not downloaded"
    exit 1
fi

echo "All assets downloaded successfully"


docker build . -t autoantibody_classifier

docker tag autoantibody_classifier 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:lambda
docker push 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:lambda


rm -rf temporary
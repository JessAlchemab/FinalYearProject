aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 189545766043.dkr.ecr.eu-west-2.amazonaws.com

# Exit on any error
set -e

echo "Starting download of assets from S3..."

# Download model and tokenizers
echo "Downloading model..."
aws s3 cp --recursive s3://alchemab-ml/autoantibody_model temporary/autoantibody_model


# Download predict script
wget -O temporary/predict.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/predict.py
wget -O temporary/analyse_metrics.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/analyse_metrics.py
wget -O temporary/utils.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/utils.py
wget -O temporary/aws_handler.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/aws_handler.py
wget -O temporary/secrets_manager.py https://raw.githubusercontent.com/JessAlchemab/FinalYearProject/refs/heads/main/machine_learning/predict/secrets_manager.py
wget -O temporary/handler.py 
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

echo "All assets downloaded successfully"


docker build --no-cache . -t autoantibody_classifier

docker tag autoantibody_classifier 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest
docker push 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest

docker tag autoantibody_classifier 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_gpu:latest
docker push 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_gpu:latest

rm -rf temporary
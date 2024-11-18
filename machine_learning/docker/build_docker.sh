aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 189545766043.dkr.ecr.eu-west-2.amazonaws.com

docker build ./docker_gpu -t autoantibody_classifier

docker tag autoantibody_classifier 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_gpu:latest
docker push 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_gpu:latest

docker tag 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_gpu:latest 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_cpu:latest
docker push 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_cpu:latest

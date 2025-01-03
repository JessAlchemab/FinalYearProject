# Use the official PyTorch image as the base
# FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
FROM mambaorg/micromamba:1-focal-cuda-11.7.1
USER root
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba create -y -n predict -f /tmp/env.yaml && \
    micromamba clean --all --yes && \
    rm -f /tmp/env.yaml
# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    wget \
    python3-pip  
#     ca-certificates \
#     git \
#     build-essential \
#     libssl-dev \
#     libncurses-dev \
#     libsqlite3-dev \
#     libreadline-dev \
#     libtk8.6 \
#     libgdm-dev \
#     libdb4o-cil-dev \
#     libpcap-dev \
#     libffi-dev \
#     libxml2-dev \
#     libxmlsec1-dev \
#     zlib1g-dev \
#     && rm -rf /var/lib/apt/lists/*

ENV TORCH_DISTRIBUTED_DEBUG=DETAIL

# Create and activate the 'predict' environment
# RUN micromamba create -n predict -y
RUN eval "$(micromamba shell hook --shell bash) "
# RUN micromamba activate
ENV CONDA_PREFIX /opt/micromamba/envs/predict
ENV PATH "$CONDA_PREFIX/bin:$PATH"
ENV PYTHONPATH /var/task

# RUN /bin/bash -c micromamba activate predict
COPY requirements.txt /tmp/

# Copy requirements and install dependencies
RUN pip --no-cache-dir install --upgrade pip && \
    pip --no-cache-dir install --upgrade awscli && \
    pip install -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

# Set the working directory
WORKDIR /app








# Get the model and the predict.py script
# COPY download_assets.sh /app/
# RUN chmod +x /app/download_assets.sh && /app/download_assets.sh

COPY temporary/autoantibody_model /app/autoantibody_model
COPY temporary/predict.py /app/predict.py
COPY temporary/utils.py /app/utils.py
COPY temporary/aws_handler.py /app/aws_handler.py
COPY temporary/analyse_metrics.py /app/analyse_metrics.py
COPY temporary/secrets_manager.py /app/secrets_manager.py
COPY temporary/handler.py /var/task/handler.py
COPY temporary/handler.py /var/tasks/handler.py


# Copy entry point
# COPY entry.py /var/task/
# COPY entry.py /var/tasks/

# Set the entry point
ENTRYPOINT ["python3", "-c"]
CMD ["import handler; handler.lambda_handler(None, None)"]

# CMD ["/app/predict.py"]

# On initialising the container make it run the script(?)
# ENTRYPOINT ["/bin/bash", "-c", "torchrun --nproc_per_node=1 /app/predict.py \
#     --input_path ${INPUT_FILE} \
#     --output_path ${OUTPUT_FILE} \
#     --tokenizer_path /app/autoantibody_model/tokenizers \
#     --model_path /app/autoantibody_model/trained_model/classifier-model \
#     --file_source aws \
#     "]
    
#docker run -e ENABLE_CUDA=1 -e INPUT_FILE=s3://alchemab-scratch/jess_scratch/autoantibody_classifier/inputs/SE_0000222.tsv -e OUTPUT_FILE=SE_0000222.tsv --rm --gpus all -it autoantibody_classifier:latest

# Build and push commands
#docker build --no-cache . -t autoantibody_classifier:latest
# aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 189545766043.dkr.ecr.eu-west-2.amazonaws.com
##password=$(aws ecr get-login-password --region eu-west-2)
##echo $password | docker login --username AWS --password-stdin 189545766043.dkr.ecr.eu-west-2.amazonaws.com
#docker tag autoantibody_classifier:latest 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest
#docker push 189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest

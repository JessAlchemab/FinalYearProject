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
    pip install awslambdaric && \
    rm -f /tmp/requirements.txt

# Set the working directory
WORKDIR /var/task

# Copy your application files

# MODEL_PATH: /app/autoantibody_model/trained_model/classifier-model
# TOKENIZER_PATH: /app/autoantibody_model/tokenizers
COPY temporary/autoantibody_model /var/task/autoantibody_model
COPY temporary/predict.py /var/task/predict.py
COPY temporary/utils.py /var/task/utils.py
COPY temporary/aws_handler.py /var/task/aws_handler.py
COPY temporary/analyse_metrics.py /var/task/analyse_metrics.py
COPY temporary/secrets_manager.py /var/task/secrets_manager.py
COPY temporary/handler.py /var/task/handler.py

# Set the Lambda Runtime Interface Client as the entry point
ENTRYPOINT [ "/usr/bin/python3", "-m", "awslambdaric" ]
CMD [ "handler.lambda_handler" ]
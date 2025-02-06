# Machine Learning

This folder contains the files used for data preparation and finetuning (in /data_preparation), the script used for predicting on a file level (/predict), the Nextflow pipeline which runs the predict script and extracts autoantibody metrics (/predict), and dockerisation required to run the Nextflow pipeline with CPU or GPU machines (in /docker).

To create an environment to run this in (runnable using conda as well as micromamba, substituting the name):
micromamba create -n predict python==3.10
micromamba activate predict
pip install -r requirements.txt

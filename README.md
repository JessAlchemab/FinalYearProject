# FinalYearProject

A repository containing the work undertaken for the final year project of the bioinformatics (data science) degree apprenticeship.

Machine learning

The primary step of this project was the development of a machine learning model finetuned from FAbCon small to distinguish between autoreactive and non-autoreactive antibodies.

Steps for the finetuning and data preparation of this step can be found in th machine_learning folder.

Additionally, a Nextflow pipeline was created to allow annotation of files of sequences and analysis of sequence metrics which may indicate autoreactivity.

To create an environment to run this in (assuming micromamba, but should work with Conda too):
micromamba create -n predict python==3.10
micromamba activate predict
pip install -r requirements.txt

Application

To make the machine learning model accessible, an application was created with a React front-end and a Serverless backend which was deployed to AWS Lambda. The code for these can be found in the autoantibody_app folder.

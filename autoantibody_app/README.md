# Application

Front end

The front end contains 3 views.

- Submit Sequence allows a user to submit a single sequence and receive a probability of that sequence being human according to the machine learning model.

- Submit File allows a user to submit a .tsv, .csv or .parquet file containing either a sequence_vh column of VH sequences OR sequence_alignment and germline_alignment_d_mask column from which can be inferred the VH sequence, backfilled. Other optional columns are v_call, c_call, cdr3_aa, and mu_count_total. All other columns will be ignored, but will still exist in the returned file. Files are uploaded to S3 and the Nextflow pipeline begins. Confirmation of the pipeline beginning can be found on the pipeline_alerts Slack channel, which will also allow users to be informed on whether the pipeline has completed.

- Reports allows a user to view the report of their file after pipeline completion, as well as downloading the newly annotated file.

To run the front-end locally:

cd client

npm i

npm run dev

A .env file must be created in the format of the .env-example file to allow the front end application to access the backend and verify user IDs. If the back end is running locally, the .env will need to reflect the address for the local API in the environment variable VITE_AUTOANTIBODY_URL.

Back end

To run the back end locally:

sls offline

To deploy the back end:

serverless deploy --stage dev

(the classifier-small backend may need the docker rebuilding and repushing. Files to do this can be found inside the classifier-small function folder.)

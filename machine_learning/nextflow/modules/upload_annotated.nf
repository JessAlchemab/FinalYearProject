process upload_annotated {
    container "189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest"
    input:
        path output_file
    script:
        """
        aws s3 cp ${output_file} ${params.s3_output_path}
        """
}
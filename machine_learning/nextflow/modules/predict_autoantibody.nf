process predict_autoantibody {
    container "189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier:latest"
    label 'gpu'  // Add this line to apply GPU configuration

    input:
        // path input_file
        tuple val(file_id), path(input_file)
    output:
        // path "autoantibody_annotated.tsv"
        tuple val(file_id), path("autoantibody_annotated.${file_id}.tsv"), emit: output_file
    script:
        println "Input file: ${input_file}" // Log the input_file value

        def args = task.ext.args ?: ''
        """
        torchrun --nproc_per_node=1 \\
        /app/predict.py \\
        --input_path "${input_file}" \\
        --output_file "autoantibody_annotated.${file_id}.tsv" \\
        --tokenizer_path /app/autoantibody_model/tokenizers \\
        --model_path /app/autoantibody_model/trained_model/classifier-model
        """
}
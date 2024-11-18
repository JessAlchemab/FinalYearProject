process METRICS_ANALYSIS {
    container "189545766043.dkr.ecr.eu-west-2.amazonaws.com/alchemab/autoantibody_classifier_cpu:latest"
    
    input:
        tuple val(file_id), path(annotated_file)
        
    script:
        println "Metrics analysis input file: ${annotated_file}" // Debug log
        """
        python3 /app/analyse_metrics.py \\
               --file_path ${annotated_file} \\
               --hash_id ${params.hash_id} \\
               --rds_table ${params.rds_table} 
        """
}
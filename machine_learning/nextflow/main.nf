#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

if (params.input_file_path) {
    ch_input = channel.value([file(params.input_file_path).baseName, file(params.input_file_path)]) 
} else {
    exit 1, 'Input file not specified!'
}

include { PREDICT_AUTOANTIBODY } from './modules/predict_autoantibody'
include { METRICS_ANALYSIS     } from './modules/metrics_analysis'

workflow {
    ch_input.view()

    PREDICT_AUTOANTIBODY(ch_input)

    METRICS_ANALYSIS(PREDICT_AUTOANTIBODY.out.output_file)
}
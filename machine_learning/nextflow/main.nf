#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

if (params.input_file_path) {
    ch_input = channel.value([file(params.input_file_path).baseName, file(params.input_file_path)]) 
} else {
    exit 1, 'Input file not specified!'
}

include { predict_autoantibody } from './modules/predict_autoantibody'
include { metrics_analysis     } from './modules/metrics_analysis'
// include { upload_annotated               } from './modules/upload_annotated'


workflow {
    ch_input.view()
    predict_autoantibody(ch_input)
    ch_predict_autoantibody = ch_input.join(predict_autoantibody.out.output_file)
    metrics_analysis(ch_predict_autoantibody)
    // upload_annotated(ch_predict_autoantibody)
}

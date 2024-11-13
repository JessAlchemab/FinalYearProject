withName: predict_autoantibody {
    publishDir = [
        path: { "${params.outdir}" },
        mode: params.publish_dir_mode,
        pattern: "*.tsv",
        saveAs: { filename -> filename.replace("${group_id}.", "") }
    ]
}

withName: metrics_analysis.nf {
    ext.args = [
        "--connection_string ${params.connection_string}"
    ]
}
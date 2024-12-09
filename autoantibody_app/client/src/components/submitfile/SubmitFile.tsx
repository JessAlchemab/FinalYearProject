import { useState } from "react";
import { InboxOutlined, QuestionCircleOutlined } from "@ant-design/icons";
import { Upload, message, Button, DraggerProps, Progress, Tooltip } from "antd";
import type { UploadChangeParam, UploadFile } from "antd/es/upload/interface";
import { s3MultipartUpload, submitBatchJob } from "../../api/autoantibodyAPI";

export const SubmitFile = () => {
  const { Dragger } = Upload;

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<UploadFile | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const justSubmitJob = async () => {
    await submitBatchJob(
      "6b19279a-08b4-4eb8-ba12-3eca8ac67687_autoantibody.parquet"
    );
  };
  const handleFileUpload = async () => {
    if (!selectedFile) {
      message.error("No file selected");
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Ensure we have the actual file object
      const file = selectedFile.originFileObj || selectedFile;
      if (!file) {
        throw new Error("Invalid file");
      }

      const path = ""; // Your desired path
      const fullPath = path + selectedFile.name;

      // Use multipart upload with progress tracking
      const response = await s3MultipartUpload(
        file as File,
        fullPath,
        (progress) => {
          setUploadProgress(Math.round(progress.percentage));
        }
      );

      message.success(`File ${selectedFile.name} uploaded successfully`);
      // Submit batch job with the hashed name from the response
      try {
        submitBatchJob(response.hashed_name).then((res) => {
          console.log(res);
          message.success(
            `Pipeline initiated successfully with name ${res.data.hash_id}. Check pipeline submission channel for progress.`,
            100
          );
        });
      } catch {
        message.error(
          `Succeeded at uploading file: ${selectedFile.name} but failed to submit pipeline.`
        );
      }

      setSelectedFile(null);
      setFileList([]);
      setUploadProgress(0);
    } catch (error) {
      message.error(`Failed to upload file: ${selectedFile.name}`);
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const draggerProps: DraggerProps = {
    name: "file",
    multiple: false,
    fileList: fileList,
    customRequest: (info: { file: any; onSuccess?: any; onError?: any }) => {
      const { file, onSuccess } = info;

      // Instead of immediately uploading, just set the selected file
      setSelectedFile(file);

      // Add file to fileList to show it in the Dragger
      const updatedFileList = [file];
      setFileList(updatedFileList);

      onSuccess(null, file);
    },
    onChange(info: UploadChangeParam<UploadFile<any>>) {
      console.log(info);
    },
    beforeUpload(file) {
      // Optional: Add any file validation here
      // For example, check file type
      const isValidType =
        file.type === "text/csv" ||
        file.type === "text/tab-separated-values" ||
        file.name.endsWith(".parquet");

      if (!isValidType) {
        message.error("You can only upload CSV, TSV, or Parquet files!");
        return Upload.LIST_IGNORE;
      }

      return true;
    },
  };

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        alignContent: "center",
        overflowY: "scroll",
      }}
    >
      <div
        style={{
          width: "50%",
          marginLeft: "auto",
          marginRight: "auto",
          display: "grid",
          gap: "2rem",
          height: "100%",
          gridTemplateRows: "max-content auto auto",
        }}
      >
        <div
          style={{
            display: "grid",
            justifyContent: "center",
          }}
        >
          <div style={{ display: "flex", flexDirection: "row" }}>
            <h4 style={{ height: "max-content", padding: "2rem" }}>
              Submit File
            </h4>
            <Tooltip
              title={
                "Submit a .csv, .tsv or .parquet file containing, at minimum, either a column 'vh_sequence' which contains a fully backfilled VH amino acid sequence, or a sequence_alignment and germline_alignment_d_mask column from which the pipeline will infer vh_sequence"
              }
            >
              <QuestionCircleOutlined />
            </Tooltip>
          </div>
        </div>
        <div
          style={{
            maxWidth: "40%",
            marginLeft: "auto",
            marginRight: "auto",
            maxHeight: "max-content",
          }}
        >
          <Dragger style={{ maxHeight: "60vh" }} {...draggerProps}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              Click or drag file to this area to upload
            </p>
            <p className="ant-upload-hint">
              Support for upload of a .tsv, .csv, or .parquet file. File must
              contain at minimum either a column 'sequence_vh' containing the
              fully backfilled VH amino acid sequence, or the columns present in
              AIRR tsv files required to backfill amino acids
              (sequence_alignment and germline_alignment_d_mask).
            </p>
            <p className="ant-upload-hint">
              Other columns which are utilized by the pipeline and will give
              extra analysis information are:
            </p>
            <ul className="ant-upload-hint">
              <li className="ant-upload-hint">v_call</li>
              <li className="ant-upload-hint">c_call</li>
              <li className="ant-upload-hint">cdr3_aa</li>
              <li className="ant-upload-hint">mu_count_total</li>
            </ul>
          </Dragger>

          {selectedFile && (
            <div style={{ marginTop: "1rem", textAlign: "center" }}>
              Selected File: {selectedFile.name}
            </div>
          )}

          {isUploading && (
            <Progress
              percent={uploadProgress}
              status={uploadProgress === 100 ? "success" : "active"}
              style={{ marginTop: "1rem" }}
            />
          )}

          <Button
            type="primary"
            onClick={handleFileUpload}
            disabled={!selectedFile || isUploading}
            loading={isUploading}
            style={{ marginTop: "1rem", width: "100%" }}
          >
            {isUploading ? "Uploading..." : "Submit"}
          </Button>
          {/* <Button
            type="primary"
            onClick={justSubmitJob}
            disabled={isUploading}
            loading={isUploading}
            style={{ marginTop: "1rem", width: "100%" }}
          >
            {"Submit"}
          </Button> */}
        </div>
      </div>
    </div>
  );
};

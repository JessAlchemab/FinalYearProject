import React, { useState } from "react";
import { InboxOutlined } from "@ant-design/icons";
import { Upload, message, Button, DraggerProps } from "antd";
import type { UploadChangeParam, UploadFile } from "antd/es/upload/interface";
import { s3UploadFile, submitBatchJob } from "../../api/autoantibodyAPI";

export const SubmitFile = () => {
  const { Dragger } = Upload;

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<UploadFile | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async () => {
    if (!selectedFile) {
      message.error("No file selected");
      return;
    }

    // setIsUploading(true);
    console.log("aa");

    // try {
    console.log(selectedFile);
    const file = selectedFile;
    if (!file) {
      throw new Error("Invalid file");
    }

    const path = ""; // Your desired path
    const fullPath = path + selectedFile.name;
    const response = await s3UploadFile(file, fullPath);

    if (response.status === 200) {
      message.success(`File ${selectedFile.name} uploaded`);

      // Submit batch job
      await submitBatchJob(response.hashed_name);

      // Clear selected file and file list
      setSelectedFile(null);
      setFileList([]);
    }
    // } catch (error) {
    //   message.error(`Failed to upload file: ${selectedFile.name}`);
    //   console.error(error);
    // } finally {
    //   setIsUploading(false);
    // }
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
        marginLeft: "auto",
        marginRight: "auto",
        padding: "1rem",
        width: "30%",
        minWidth: "200px",
      }}
    >
      <Dragger {...draggerProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          Click or drag file to this area to upload
        </p>
        <p className="ant-upload-hint">
          Support for upload of a .tsv, .csv, or .parquet file. File must
          contain at minimum a column 'sequence_vh' containing the VH amino acid
          sequence.
        </p>
        <p className="ant-upload-hint">
          Other columns which are utilized by the pipeline and will give extra
          analysis are:
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

      <Button
        type="primary"
        onClick={handleFileUpload}
        disabled={!selectedFile || isUploading}
        loading={isUploading}
        style={{ marginTop: "1rem", width: "100%" }}
      >
        {isUploading ? "Uploading..." : "Submit"}
      </Button>
    </div>
  );
};

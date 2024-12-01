/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { AxiosRequestConfig } from "axios";
import { ClassifierResponse } from "../libs/types";
import { useUserStore } from "../+state/UserSlice";

const ERROR_MSG = "Problem occured while trying to fetch data from the server.";

const httpClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL_PROTOCOL}://${
    import.meta.env.VITE_AUTOANTIBODY_URL
  }/`,
});

async function apiRequest(
  url: string,
  config?: AxiosRequestConfig,
  type?: "GET" | "POST" | "DELETE",
  postData?: any
): Promise<any> {
  let res = { status: 200, data: null, message: ERROR_MSG };
  if (type === "GET") {
    res = await httpClient.get(url, config);
  } else {
    res = await httpClient.post(url, postData, config);
  }

  if (res.status !== 200) throw Error(ERROR_MSG);
  return { data: res.data };
}

export async function classifySmall(body: { sequence: string }) {
  const response = await apiRequest(`classify-small`, undefined, "POST", body);
  return response as { data: ClassifierResponse };
}

export async function s3UploadFile(selectedFile: any, path: string) {
  const { userData } = useUserStore.getState();
  const headers = {
    Authorization: `Bearer ${userData?.idToken}`,
    "x-access-token": userData?.accessToken as string,
  };
  try {
    // Get the actual file object - handle both direct file uploads and Upload component's format
    const actualFile =
      selectedFile.file?.originFileObj ||
      selectedFile.originFileObj ||
      selectedFile.file ||
      selectedFile;
    // Get the content type
    const contentType = actualFile.type || "application/x-parquet";

    // Get the presigned URL
    const response = await apiRequest<FileUploadResponse>(
      `get-upload-url/?file_path=${path}`,
      {
        headers: {
          Authorization: headers["Authorization"],
          "Content-Type": contentType,
        },
      },
      "GET"
    );

    // const { url: presignedUrl, hashed_name } = response.data;

    // Debug logging
    console.log("Content-Type being sent:", contentType);
    console.log("File object structure:", actualFile);

    // Upload to S3
    const uploadResponse = await fetch(response.data.url, {
      method: "PUT",
      // Important: Send the actual File object, not the wrapper
      body: actualFile,
      headers: {
        "Content-Type": contentType,
      },
    });

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      console.error("S3 Upload Error:", {
        status: uploadResponse.status,
        statusText: uploadResponse.statusText,
        errorText,
        requestHeaders: uploadResponse.headers,
      });
      throw new Error(
        `Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`
      );
    }
    return response.data;
  } catch (error) {
    console.error("Error uploading file to S3:", error);
    throw error;
  }
}

export async function submitBatchJob(hashed_name: any) {
  const response = await apiRequest(`submit-pipeline`, undefined, "POST", {
    input_file: hashed_name,
    revision: "v1.0.18",
  });
  return response as { data: ClassifierResponse };
}

export async function getReportList(searchTerm: string = "") {
  const response = await apiRequest(`get-runs`, undefined, "POST", {
    search_string: searchTerm,
  });
  return response;
}

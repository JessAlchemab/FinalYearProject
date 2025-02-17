/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { AxiosRequestConfig } from "axios";
import { ClassifierResponse } from "../libs/types";
import { useUserStore } from "../+state/UserSlice";

const ERROR_MSG = "Problem occured while trying to fetch data from the server.";

const httpClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL_PROTOCOL}://${
    import.meta.env.VITE_AUTOANTIBODY_URL
  }/`,
  // baseURL: `${import.meta.env.VITE_API_URL_PROTOCOL}://${
  //   import.meta.env.VITE_AUTOANTIBODY_URL
  // }/`,
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
    const response = await apiRequest(
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
    // THIS LINE NEEDS CHANGING EVERY TIME A REVISION IS MADE
    revision: "v1.0.28",
  });
  return response as { data: { hash_id: string } };
}

export async function getReportList(searchTerm: string = "") {
  const response = await apiRequest(`get-runs`, undefined, "POST", {
    search_string: searchTerm,
  });
  return response;
}

export async function getReportData(name: string = "") {
  const response = await apiRequest(`get-run-data`, undefined, "POST", {
    name: name,
  });
  return response;
}

export async function s3MultipartUpload(
  file: File,
  path: string,
  onProgress?: (progress: { percentage: number }) => void
) {
  const { userData } = useUserStore.getState();

  // 20MB in each chunk
  const CHUNK_SIZE = 20 * 1024 * 1024;

  try {
    // Attempt to get a new multipart upload URL
    const multipartResponse = await apiRequest(
      `get-multipart-upload-url/?file_path=${path}`,
      {
        headers: {
          Authorization: `Bearer ${userData?.idToken}`,
          "x-access-token": userData?.accessToken,
          "Content-Type": file.type || "application/octet-stream",
        },
      },
      "GET"
    );

    const { uploadId, hashed_name } = multipartResponse.data;

    // Track upload parts
    const uploadedParts: { ETag: string; PartNumber: number }[] = [];

    // Total file size for progress tracking
    const totalSize = file.size;
    let uploadedSize = 0;

    // Upload parts
    for (let partNumber = 1; ; partNumber++) {
      const start = (partNumber - 1) * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);

      // Break if we've reached the end of the file
      if (start >= file.size) break;

      const chunk = file.slice(start, end);

      try {
        // Get presigned URL for this specific part
        const partUrlResponse = await apiRequest(
          `get-multipart-upload-part-url/?file_path=${hashed_name}&uploadId=${uploadId}&partNumber=${partNumber}`,
          {
            headers: {
              Authorization: `Bearer ${userData?.idToken}`,
              "x-access-token": userData?.accessToken,
            },
          },
          "GET"
        );

        // Upload the part
        const uploadResponse = await fetch(partUrlResponse.data.url, {
          method: "PUT",
          body: chunk,
          headers: {
            "Content-Type": file.type || "application/octet-stream",
          },
        });

        if (!uploadResponse.ok) {
          // Detailed error logging
          const errorText = await uploadResponse.text();
          console.error(`Part upload failed: Part ${partNumber}`, {
            status: uploadResponse.status,
            statusText: uploadResponse.statusText,
            errorText,
          });
          throw new Error(`Part upload failed: Part ${partNumber}`);
        }

        // Store the ETag for completing the multipart upload
        const eTag = uploadResponse.headers.get("ETag") || "";
        uploadedParts.push({ ETag: eTag, PartNumber: partNumber });

        // Update progress
        uploadedSize += chunk.size;
        if (onProgress) {
          onProgress({
            percentage: (uploadedSize / totalSize) * 100,
          });
        }
      } catch (partUploadError) {
        // If a part upload fails, attempt to abort the entire upload
        try {
          await apiRequest(
            `abort-multipart-upload/?file_path=${hashed_name}&uploadId=${uploadId}`,
            {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${userData?.idToken}`,
                "x-access-token": userData?.accessToken,
              },
            }
          );
        } catch (abortError) {
          console.error("Failed to abort multipart upload", abortError);
        }

        // Re-throw the original error
        throw partUploadError;
      }
    }

    // const response = await apiRequest(`get-runs`, undefined, "POST", {
    //   search_string: searchTerm,
    // });

    // Complete the multipart upload
    const completeUploadResponse = await apiRequest(
      `complete-multipart-upload/?file_path=${hashed_name}&uploadId=${uploadId}`,
      {
        headers: {
          Authorization: `Bearer ${userData?.idToken}`,
          "x-access-token": userData?.accessToken,
          "Content-Type": "application/json",
        },
      },
      "POST",
      { parts: uploadedParts }
    );
    console.log(completeUploadResponse);
    return completeUploadResponse.data;
  } catch (error) {
    console.error("Multipart upload error:", error);
    throw error;
  }
}

export async function queryAthena(): Promise<any> {
  const response: any = await apiRequest(`query-athena`, undefined, "GET");
  const result = await poll(response.data.queryId, 3000);
  return result;
}

export async function poll(queryId: any, ms: number) {
  // const totalData = [];
  // let columns;
  // for (const queryId of queryIds) {
  let status = await checkStatus(queryId);
  console.log(status);
  while (status === "QUEUED" || status === "RUNNING") {
    await wait(ms);
    status = await checkStatus(queryId);
  }
  if (status === "CANCELLED") {
    return { data: "Cancelled" };
  }
  if (status === "SUCCEEDED") {
    // let pageNumber = 1;
    // let hasMore = true;
    // while (hasMore) {
    const result = await fetchData(queryId, 1);
    // if (pageNumber === 1) {
    //   columns = result.columns;
    // }
    // totalData.push(...result.data);
    // hasMore = result.has_more;
    // pageNumber++;
    return result;
  }
}

function wait(ms = 1000) {
  return new Promise((resolve) => {
    console.log(`waiting ${ms} ms...`);
    setTimeout(resolve, ms);
  });
}
async function checkStatus(queryId: string): Promise<string> {
  const response: any = await apiRequest("/status", undefined, "POST", {
    queryId: queryId,
  });
  return response.data;
}

async function fetchData(queryId: string, pageNumber: number) {
  const response: any = await apiRequest(
    "/get-athena-response",
    undefined,
    "POST",
    {
      queryId: queryId,
      page_number: pageNumber,
    }
  );
  return response.data.results;
  // has_more: response.data.has_more,
  // columns: response.data.columns,
}

export async function downloadFile(fileHash: string) {
  const response = await apiRequest(`download-file`, undefined, "POST", {
    hashId: fileHash,
  });
  return response;
}

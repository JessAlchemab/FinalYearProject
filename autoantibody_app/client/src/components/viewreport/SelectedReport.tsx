import { downloadFile } from "../../api/autoantibodyAPI";
import { Button, message, Table } from "antd";
import { ColumnsType } from "antd/es/table";
import { Spin, Tooltip } from "antd";
import ProbabilityHistogram from "./ProbabilityHistogram";
import { DownloadOutlined, QuestionCircleOutlined } from "@ant-design/icons";

interface Properties {
  file_hash: any;
  reportContent: any;
  athenaContent: any;
  athenaLoading: boolean;
}

interface DataItem {
  metric: string;
  statistic: unknown;
}

export const SelectedReport = (props: Properties) => {
  const reasoningObj: { [name: string]: { info: string; name: string } } = {
    total_rows: {
      info: "Total number of rows from dataset",
      name: "Total Sequences",
    },
    human_rows: {
      info: "Number of rows which the autoantibody classifier model has assigned 'human' with over 99% confidence",
      name: "Predicted Human Sequences",
    },
    ighv4_34_percentage: {
      info: "Percentage of sequences with IGHV4-34 V-gene usage. Increased IGHV4-34 usage is associated with autoreactivity",
      name: "IGHV4-34 %",
    },
    ighv3_30_percentage: {
      info: "Percentage of sequences with IGHV3-30 V-gene usage. Decreased IGHV3-30 usage is associated with autoreactivity",
      name: "IGHV3-30 %",
    },
    ighg_percentage: {
      info: "Higher levels of IGHG antibodies are seen in autoreactive repertoires",
      name: "IGHG %",
    },
    ighg1_percentage: {
      info: "Elevated IGHG1 levels have been associated with some autoimmune disorders",
      name: "IGHG1 %",
    },
    ighg2_percentage: {
      info: "Elevated IGHG2 levels have been associated with some autoimmune disorders",
      name: "IGHG2 %",
    },
    ighg3_percentage: {
      info: "Elevated IGHG3 levels have been associated with some autoimmune disorders",
      name: "IGHG3 %",
    },
    ighg4_percentage: {
      info: "Elevated IGHG4 levels have been associated with some autoimmune disorders",
      name: "IGHG4 %",
    },
    average_cdr3_length: {
      info: "Antibody sequences with longer CDR3 length may be more likely to demonstrate autoreactivity",
      name: "Avg. CDR3 Length",
    },
    average_mu_count: {
      info: "Antibody sequences with more mutations and deviation from germline are more likely to demonstrate autoreactivity",
      name: "Avg. Mutation Count",
    },
    human_prediction_percentage: {
      info: "The percentage of sequences from the input file which have been assigned 'human' with a confidence of over 99%",
      name: "% Human Sequences",
    },
    probability_histogram: {
      info: "A histogram displaying the distribution of probabilities the autoantibody classifier model assigned to sequences in the input file.",
      name: "Probability Distribution",
    },
    date: { info: "The date on which the file completed piping", name: "Date" },
  };
  // Convert the object to an array of key-value pairs for the table
  const tableData: DataItem[] = props.reportContent
    ? Object.entries(props.reportContent)
        .filter(([key]) => key !== "hash_id" && key !== "probability_histogram") // Optionally exclude hash_id
        .map(([key, value]) => ({
          metric: key,
          statistic: value,
          reasoning: reasoningObj[key as keyof Object]["info"],
          athena:
            props.athenaContent && props.athenaContent[key]
              ? props.athenaContent[key]
              : null,
        }))
    : [];

  const columns: ColumnsType<DataItem> = [
    {
      title: "Metric",
      dataIndex: "metric",
      key: "metric",
      width: "10rem",

      render: (text) => reasoningObj[text]["name"],
    },
    {
      title: "Info",
      dataIndex: "reasoning",
      key: "reasoning",
      width: "5rem",
      render: (value) => (
        <Tooltip title={value}>
          <QuestionCircleOutlined />
        </Tooltip>
      ),
    },
    {
      title: "Sequences From File",
      dataIndex: "statistic",
      key: "statistic",
      width: "15rem",

      render: (value) =>
        typeof value === "number"
          ? value.toFixed(value % 1 === 0 ? 0 : 2)
          : value,
    },
    {
      title: "Sequences From All Controls",
      dataIndex: "athena",
      key: "athena",
      width: "15rem",

      render: (value) =>
        props.athenaLoading ? (
          <Spin size="small" />
        ) : value ? (
          typeof value === "string" && !isNaN(parseFloat(value)) ? (
            parseFloat(value).toFixed(value.includes(".") ? 2 : 0)
          ) : (
            value
          )
        ) : (
          "N/A"
        ),
    },
  ];

  const fileDownload = (hashId: string) => {
    downloadFile(hashId)
      .then((res) => {
        const presignedUrl = res.data.presignedUrl;
        const link = document.createElement("a");
        link.href = presignedUrl;
        const filename = presignedUrl.split("/").pop().split("?")[0];
        link.download = filename || "downloaded_file";

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
      })
      .catch((error) => {
        message.error("Failed to download file");
        console.error("Download error:", error);
      });
  };

  return props.reportContent ? (
    <div
      style={{
        display: "grid",
        gap: "2rem",
        gridTemplateRows: "max-content",
        justifyItems: "center",
        padding: "2rem",
      }}
    >
      <h2>Report for {props.file_hash}</h2>
      <div>
        <h4>Download annotated file</h4>
        <Tooltip title={"Downlaod annotated file from s3"}>
          <Button
            style={{ width: "4rem", height: "4rem" }}
            onClick={() => fileDownload(props.file_hash)}
          >
            <DownloadOutlined style={{ fontSize: "3rem" }} />
          </Button>
        </Tooltip>
      </div>
      <div>
        <h4>Metrics of input file vs. metrics across all controls</h4>
        <Table
          columns={columns}
          dataSource={tableData}
          pagination={false}
          size="small"
          style={{ width: "max-content" }}
        />
      </div>
      <div>
        <h4>Distribution of model confidence across file sequences</h4>
        <ProbabilityHistogram
          data={JSON.parse(props.reportContent.probability_histogram)}
        />
      </div>
    </div>
  ) : null;
};

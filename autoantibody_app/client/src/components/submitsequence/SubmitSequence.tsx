import { Space, Input, Button, Spin, Table, Tooltip } from "antd";
import { useState } from "react";
import { classifySmall } from "../../api/autoantibodyAPI";
import { ClassifierResponse } from "../../libs/types";
import { QuestionCircleOutlined } from "@ant-design/icons";

export const SubmitSequence = () => {
  const [sequence, setSequence] = useState<string>("");
  const [classifierResponse, setClassifierResponse] =
    useState<null | ClassifierResponse>(null);
  const [responseLoading, setResponseLoading] = useState<boolean>(false);

  const submitSequence = () => {
    classifySmall({ sequence: sequence });
    setResponseLoading(true);
    try {
      classifySmall({ sequence: sequence }).then(
        (res: { data: ClassifierResponse }) => {
          console.log(res.data);
          setClassifierResponse(res.data);
          setResponseLoading(false);
        }
      );
    } catch {
      setResponseLoading(false);
    }
  };

  const columns = [
    {
      title: "Input Sequence",
      dataIndex: "inputSeq",
      key: "inputSeq",
      width: 200,
      ellipsis: true,
    },
    {
      title: "Human Probability",
      dataIndex: "prob",
      key: "prob",
      width: 200,
    },
  ];

  const dataSource = [
    {
      key: "1",
      inputSeq: classifierResponse?.sequence_vh_x,
      prob: classifierResponse?.human_probability,
    },
  ];

  console.log(sequence);
  return (
    <div
      style={{
        width: "50%",
        marginLeft: "auto",
        marginRight: "auto",
        display: "grid",
        gap: "6rem",
        height: "100%",
        gridTemplateRows: "max-content auto",
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
            Submit a VH amino acid sequence
          </h4>
          <Tooltip
            title={
              "Submit a fully backfilled VH sequence to predict the machine learning model's confidence in its autoreactivity"
            }
          >
            <QuestionCircleOutlined />
          </Tooltip>
        </div>
      </div>
      <div
        style={{
          height: "50%",
          display: "grid",
          gap: "2rem",
          alignItems: "center",
          gridTemplateRows: "auto max-content",
        }}
      >
        <Space.Compact style={{ width: "100%" }}>
          <Input
            defaultValue=""
            onChange={(evt) => setSequence(evt.target.value)}
          />
          <Button
            type="primary"
            onClick={() => submitSequence()}
            disabled={sequence.length < 1 || responseLoading}
          >
            Predict
          </Button>
        </Space.Compact>
        {responseLoading ? <Spin /> : <></>}
        {classifierResponse && !responseLoading ? (
          <Table dataSource={dataSource} columns={columns} pagination={false} />
        ) : (
          <></>
        )}
      </div>
    </div>
  );
};

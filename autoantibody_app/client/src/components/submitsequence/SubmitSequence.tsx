import { Space, Input, Button, Spin, Table } from "antd";
import { useState } from "react";
import { classifySmall } from "../../api/autoantibodyAPI";
import { ClassifierResponse } from "../../libs/types";

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
        gap: "2rem",
        height: "100%",
        gridTemplateRows: "max-content auto",
      }}
    >
      <h4 style={{ height: "max-content" }}>Submit a VH amino acid sequence</h4>
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
            Submit
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

import { Button } from "antd";
import { useNavigate } from "react-router-dom";

export const FrontPage = () => {
  const navigate = useNavigate();

  return (
    <>
      <div
        style={{
          height: "100%",
          display: "grid",
          gridTemplateRows: "max-content auto",
        }}
      >
        <h2 style={{ padding: "0.5rem" }}>Select Workflow</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "auto auto auto",
            alignItems: "center",
            height: "80%",
            width: "100%",
            gap: "3rem",
            padding: "3rem",
          }}
        >
          <Button
            onClick={() => {
              let path = `submit-sequence`;
              navigate(path);
            }}
          >
            <a>Submit Sequence</a>
          </Button>
          <Button
            onClick={() => {
              let path = `submit-file`;
              navigate(path);
            }}
          >
            <a>Submit File</a>
          </Button>
          <Button
            onClick={() => {
              let path = `view-report`;
              navigate(path);
            }}
          >
            <a>View Reports</a>
          </Button>
        </div>
      </div>
    </>
  );
};

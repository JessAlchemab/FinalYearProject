import { Button } from "antd";
import { useNavigate } from "react-router-dom";
import SingleSequenceLogo from "../../assets/sequence.svg?react";
import FileLogo from "../../assets/file.svg?react";
import ReportLogo from "../../assets/report.svg?react";

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
            style={{
              display: "grid",
              gridTemplateRows: "auto auto",
              height: "max-content",
              gap: "2rem",
              padding: "1rem",
            }}
          >
            <a>Submit Sequence</a>
            <SingleSequenceLogo />
          </Button>
          <Button
            onClick={() => {
              let path = `submit-file`;
              navigate(path);
            }}
            style={{
              display: "grid",
              gridTemplateRows: "auto auto",
              height: "max-content",
              gap: "2rem",
              padding: "1rem",
            }}
          >
            <a>Submit File</a>
            <FileLogo />
          </Button>
          <Button
            onClick={() => {
              let path = `view-report`;
              navigate(path);
            }}
            style={{
              display: "grid",
              gridTemplateRows: "auto auto",
              height: "max-content",
              gap: "2rem",
              padding: "1rem",
            }}
          >
            <a>File Download and Reports</a>
            <ReportLogo />
          </Button>
        </div>
      </div>
    </>
  );
};

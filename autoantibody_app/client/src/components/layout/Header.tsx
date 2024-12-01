import { HomeOutlined } from "@ant-design/icons";
import { Button } from "antd";
import { useNavigate } from "react-router-dom";
import "./Header.css";

export const HeaderBar = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        alignContent: "center",
        display: "grid",
        height: "100%",
        gridTemplateColumns: "max-content auto",
        gap: "1rem",
      }}
    >
      <Button
        onClick={() => {
          const path = "/";
          navigate(path);
        }}
        className="invisible-button"
      >
        <HomeOutlined
          style={{
            height: "100%",
            width: "100%",
            marginTop: "auto",
            marginBottom: "auto",
            marginLeft: "1rem",
            color: "white",
            fill: "white",
          }}
        />
      </Button>
    </div>
  );
};

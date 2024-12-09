import { Menu } from "antd";
import { HomeOutlined } from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import ALogo from "../../assets/a_logo.svg?react";

export const NavigationMenu = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick = (path: string) => {
    navigate(path);
  };

  const getSelectedKey = () => {
    switch (location.pathname) {
      case "/submit-sequence":
        return ["sequence"];
      case "/submit-file":
        return ["submit-file"];
      case "/view-report":
        return ["reports"];
      default:
        return [];
    }
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "auto max-content",
        gap: "1rem",
      }}
    >
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[]}
        style={{ flex: 1, minWidth: 0 }}
      >
        <Menu.Item key="title" onClick={() => handleMenuClick("/")}>
          <span
            style={{
              alignItems: "center",
              justifyItems: "center",
              display: "grid",
              gridTemplateColumns: "auto auto",
            }}
          >
            <ALogo style={{ height: "2rem", width: "2rem" }} />
            utoantibody Classifier
          </span>
        </Menu.Item>
        <Menu.Item />
      </Menu>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={getSelectedKey()}
        style={{
          flex: 1,
          minWidth: 0,
          width: "30rem",
          justifyContent: "end",
        }}
      >
        <Menu.Item
          key="sequence"
          onClick={() => handleMenuClick("/submit-sequence")}
        >
          Sequence
        </Menu.Item>
        <Menu.Item
          key="submit-file"
          onClick={() => handleMenuClick("/submit-file")}
        >
          Submit File
        </Menu.Item>
        <Menu.Item
          key="reports"
          onClick={() => handleMenuClick("/view-report")}
        >
          Reports
        </Menu.Item>
        <Menu.Item
          key="home"
          icon={<HomeOutlined />}
          onClick={() => handleMenuClick("/")}
        />
      </Menu>
    </div>
  );
};

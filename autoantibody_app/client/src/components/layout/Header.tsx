import { Menu } from "antd";
import { HomeOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

export const NavigationMenu = () => {
  const navigate = useNavigate();

  const handleMenuClick = (path: string) => {
    navigate(path);
  };

  return (
    <Menu
      theme="dark"
      mode="horizontal"
      defaultSelectedKeys={["2"]}
      style={{ flex: 1, minWidth: 0 }}
    >
      <Menu.Item
        key="home"
        icon={<HomeOutlined />}
        onClick={() => handleMenuClick("/")}
      />
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
      <Menu.Item key="reports" onClick={() => handleMenuClick("/view-report")}>
        Reports
      </Menu.Item>
    </Menu>
  );
};

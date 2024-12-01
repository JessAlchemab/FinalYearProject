import { Button, ConfigProvider, Layout } from "antd";
import "./App.css";
// import { Sidebar } from "./components/Sidebar";
// import { HeaderBar } from "./components/HeaderBar";
// import { HtmlViewer } from "./components/HtmlViewer";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
// import { DiseaseData } from "../../libs/types";
import { useState } from "react";
import { FrontPage } from "./components/frontpage/FrontPage";
import { SubmitSequence } from "./components/submitsequence/SubmitSequence";
import { SubmitFile } from "./components/submitfile/SubmitFile";
import { ViewReport } from "./components/viewreport/ViewReport";
import { HeaderBar } from "./components/layout/Header";

function App() {
  const [htmlId, setHtmlId] = useState<string>("");
  // const [filesData, setFilesData] = useState<DiseaseData[]>([]);
  const { Header, Sider, Content } = Layout;
  const headerStyle: React.CSSProperties = {
    textAlign: "center",
    color: "#fff",
    height: 80,
    paddingInline: 0,
    backgroundColor: "#8a1253",
  };

  const siderStyle: React.CSSProperties = {
    textAlign: "center",
    color: "#fff",
    // maxWidth: "300px !important",
    // width: "20%",
    // flex: "auto auto auto",
    resize: "horizontal",
    overflow: "hidden",
    display: "block",
  };

  const layoutStyle = {
    overflow: "hidden",
    height: "100%",
    width: "100%",
  };

  // const contentStyle: React.CSSProperties = {
  //   textAlign: "center",
  //   minHeight: 120,
  //   lineHeight: "120px",
  //   color: "#fff",
  //   paddingRight: "1rem",
  //   paddingLeft: "1rem",
  //   borderLeft: "2px solid black",
  // };

  return (
    <>
      <ConfigProvider
        theme={{
          token: {
            borderRadius: 2,
            fontFamily: "sans-serif",
          },
          components: {
            Modal: {
              titleFontSize: 22,
            },
          },
        }}
      >
        <Router>
          <div style={{ height: "100vh", width: "100vw" }}>
            <Layout style={layoutStyle}>
              <Header style={headerStyle}>
                <HeaderBar />
              </Header>
              <Layout style={{ height: "100%" }}>
                {/* <Sider style={siderStyle} width={250}> */}
                {/* <Sidebar setHtmlId={setHtmlId} setFilesData={setFilesData} /> */}
                {/* </Sider> */}
                <Content
                // style={contentStyle}
                >
                  <Routes>
                    <Route path="/" element={<FrontPage />} />
                    <Route
                      path="/submit-sequence"
                      element={<SubmitSequence />}
                    />
                    <Route path="/submit-file" element={<SubmitFile />} />
                    <Route path="/view-report" element={<ViewReport />} />
                    <Route
                      path="/view-report/:reportId"
                      element={<ViewReport />}
                    />
                    <Route path="*" element={<Navigate to="/" />} />
                  </Routes>
                </Content>
              </Layout>
            </Layout>
          </div>
        </Router>
      </ConfigProvider>
    </>
  );
}

export default App;

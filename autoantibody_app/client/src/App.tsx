import { ConfigProvider, Layout } from "antd";
import "./App.css";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import { FrontPage } from "./components/frontpage/FrontPage";
import { SubmitSequence } from "./components/submitsequence/SubmitSequence";
import { SubmitFile } from "./components/submitfile/SubmitFile";
import { ViewReport } from "./components/viewreport/ViewReport";
import { NavigationMenu } from "./components/layout/Header";

function App() {
  const { Header, Content } = Layout;

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
          <Layout style={{ height: "100vh", width: "100vw" }}>
            <Header>
              <NavigationMenu />
            </Header>
            <Layout style={{ height: "100%" }}>
              <Content>
                <Routes>
                  <Route path="/" element={<FrontPage />} />
                  <Route path="/submit-sequence" element={<SubmitSequence />} />
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
        </Router>
      </ConfigProvider>
    </>
  );
}

export default App;

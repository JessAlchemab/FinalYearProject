import { useEffect, useState } from "react";
import {
  getReportData,
  getReportList,
  queryAthena,
} from "../../api/autoantibodyAPI";
import { Empty, Layout, Menu, Spin } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import Sider from "antd/es/layout/Sider";
import { SelectedReport } from "./SelectedReport";

type ReportItem = { hash_id: string; date: string };

export const ViewReport = () => {
  const { reportId } = useParams<{ reportId: string }>();

  const [reportList, setReportList] = useState<ReportItem[]>([]);
  const [sidebarLoading, setSidebarLoading] = useState<boolean>(false);
  const [reportContentLoading, setReportContentLoading] =
    useState<boolean>(false);
  const [athenaContentLoading, setAthenaContentLoading] =
    useState<boolean>(false);
  const [reportContent, setReportContent] = useState(null);
  const [athenaContent, setAthenaContent] = useState(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(
    reportId || null
  );
  const navigate = useNavigate();

  // First useEffect to load report list
  useEffect(() => {
    setSidebarLoading(true);

    getReportList("")
      .then((res) => {
        const reports = res.data.data;
        setReportList(reports);
        setSidebarLoading(false);

        // If there's a reportId in the URL and it exists in the report list
        if (
          reportId &&
          reports.some(
            (report: { hash_id: string }) => report.hash_id === reportId
          )
        ) {
          setSelectedKey(reportId);
        }
      })
      .catch((error) => {
        console.error("Error fetching report list:", error);
        setSidebarLoading(false);
      });
  }, []);

  // Second useEffect to load report content
  useEffect(() => {
    setReportContentLoading(true);
    const reportName = selectedKey || reportId;
    if (reportName) {
      getReportData(reportName)
        .then((res) => {
          setReportContent(res.data.data);
          setReportContentLoading(false);
        })
        .catch((error) => {
          console.error("Error fetching report data:", error);
          setReportContentLoading(false);
        });
    }
  }, [selectedKey, reportId]);
  useEffect(() => {
    setAthenaContentLoading(true);
    const reportName = selectedKey || reportId;
    if (reportName) {
      queryAthena()
        .then((res) => {
          console.log(res);
          setAthenaContent(res);
          setAthenaContentLoading(false);
        })
        .catch((error) => {
          console.error("Error fetching report data:", error);
          setAthenaContentLoading(false);
        });
    }
  }, [selectedKey, reportId]);

  const handleReportSelect = (info: { key: string }) => {
    const selectedReport = reportList.find(
      (report) => report.hash_id === info.key
    );
    if (selectedReport) {
      setSelectedKey(info.key);
      navigate(`/view-report/${info.key}`);
    }
  };

  return (
    <Layout className="h-screen" style={{ height: "100%" }}>
      <Sider width={250} theme="light">
        {sidebarLoading ? (
          <div
            className="flex justify-center items-center h-full"
            style={{ height: "100%", alignItems: "center", display: "flex" }}
          >
            <div style={{ width: "100%" }}>
              <Spin size="large" />
            </div>
          </div>
        ) : (
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={selectedKey ? [selectedKey] : []}
            onSelect={handleReportSelect}
            style={{ height: "100%" }}
          >
            <Menu.Item style={{ pointerEvents: "none" }} key={"title"}>
              <h4>Available Reports</h4>
            </Menu.Item>
            {reportList.map((report) => (
              <Menu.Item key={report.hash_id}>
                {report.hash_id}
                <br />
              </Menu.Item>
            ))}
          </Menu>
        )}
      </Sider>
      <Layout.Content
        style={{ height: "100%", alignContent: "center", overflowY: "scroll" }}
      >
        {selectedKey ? (
          reportContentLoading ? (
            <div className="flex justify-center items-center h-full">
              <Spin size="large" />
            </div>
          ) : (
            reportContent && (
              <SelectedReport
                file_hash={selectedKey}
                reportContent={reportContent}
                athenaContent={athenaContent}
                athenaLoading={athenaContentLoading}
              />
            )
          )
        ) : (
          <Empty description={"No report selected"} />
        )}
      </Layout.Content>
    </Layout>
  );
};

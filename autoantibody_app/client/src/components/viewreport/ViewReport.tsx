import { useEffect, useState } from "react";
import { getReportList } from "../../api/autoantibodyAPI";
import { Spin } from "antd";
type ReportItem = { name: string; date: string };
export const ViewReport = () => {
  const [reportList, setReportList] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  useEffect(() => {
    setLoading(true);
    getReportList("").then((res) => {
      setReportList(res.data);
      console.log(res.data);
      setLoading(false);
    });
  }, []);
  return <div>{loading ? <Spin /> : <></>}</div>;
};

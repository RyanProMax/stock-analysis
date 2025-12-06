import { useState } from 'react';
import { Layout, Typography, Spin, Empty } from 'antd';
import { StockAnalysisForm } from './components/StockAnalysisForm';
import { StockReportCard } from './components/StockReportCard';
import type { AnalysisReport } from './types';
import 'antd/dist/reset.css';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  const [reports, setReports] = useState<AnalysisReport[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAnalysisComplete = (newReports: AnalysisReport[]) => {
    setReports(newReports);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <Title level={3} style={{ color: '#fff', margin: 0 }}>
          股票分析系统
        </Title>
      </Header>
      <Content style={{ padding: '24px', background: '#f0f2f5' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <StockAnalysisForm
            onAnalysisComplete={handleAnalysisComplete}
            loading={loading}
            setLoading={setLoading}
          />
          
          {loading && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Spin size="large" tip="正在分析股票数据..." />
            </div>
          )}

          {!loading && reports.length === 0 && (
            <Empty
              description="请输入股票代码开始分析"
              style={{ marginTop: 60 }}
            />
          )}

          {!loading && reports.length > 0 && (
            <div>
              {reports.map((report) => (
                <StockReportCard key={report.symbol} report={report} />
              ))}
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
}

export default App;

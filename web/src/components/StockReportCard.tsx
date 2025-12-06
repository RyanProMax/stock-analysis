import { Card, Tag, Progress, Typography, Space, Divider, Empty } from 'antd';
import { TrendingUpOutlined, TrendingDownOutlined } from '@ant-design/icons';
import type { AnalysisReport } from '../types';

const { Title, Text, Paragraph } = Typography;

interface StockReportCardProps {
  report: AnalysisReport;
}

export const StockReportCard: React.FC<StockReportCardProps> = ({ report }) => {
  const getFearGreedColor = (index: number) => {
    if (index < 40) return 'success';
    if (index > 60) return 'error';
    return 'warning';
  };

  const technicalFactors = report.factors.filter((f) => f.category === '技术面');
  const fundamentalFactors = report.factors.filter((f) => f.category === '基本面');

  return (
    <Card
      style={{ marginBottom: 24 }}
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            {report.stock_name || report.symbol}
          </Title>
          <Tag color="blue">{report.symbol}</Tag>
          <Text strong style={{ color: '#1890ff', fontSize: 18 }}>
            ¥{report.price.toFixed(2)}
          </Text>
        </Space>
      }
    >
      {/* 贪恐指数 */}
      <Card size="small" style={{ marginBottom: 16, backgroundColor: '#fafafa' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>贪恐指数</Text>
          <Progress
            percent={report.fear_greed.index}
            status={getFearGreedColor(report.fear_greed.index) as any}
            format={(percent) => `${percent?.toFixed(1)} (${report.fear_greed.label})`}
          />
        </Space>
      </Card>

      <Divider orientation="left">技术面因子</Divider>
      {technicalFactors.length > 0 ? (
        <div style={{ marginBottom: 16 }}>
          {technicalFactors.map((factor) => (
            <FactorItem key={factor.key} factor={factor} />
          ))}
        </div>
      ) : (
        <Empty description="暂无技术面因子数据" size="small" />
      )}

      <Divider orientation="left">基本面因子</Divider>
      {fundamentalFactors.length > 0 ? (
        <div>
          {fundamentalFactors.map((factor) => (
            <FactorItem key={factor.key} factor={factor} />
          ))}
        </div>
      ) : (
        <Empty description="暂无基本面因子数据" size="small" />
      )}
    </Card>
  );
};

interface FactorItemProps {
  factor: {
    key: string;
    name: string;
    status: string;
    bullish_signals: Array<{ factor: string; message: string }>;
    bearish_signals: Array<{ factor: string; message: string }>;
  };
}

const FactorItem: React.FC<FactorItemProps> = ({ factor }) => {
  return (
    <Card
      size="small"
      style={{ marginBottom: 12 }}
      title={
        <Space>
          <Text strong>{factor.name}</Text>
          <Tag>{factor.status || '-'}</Tag>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {factor.bullish_signals.length > 0 && (
          <div>
            <Text type="success" strong>
              <TrendingUpOutlined /> 看多信号：
            </Text>
            <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
              {factor.bullish_signals.map((signal, idx) => (
                <li key={idx}>
                  <Text type="success">{signal.message}</Text>
                </li>
              ))}
            </ul>
          </div>
        )}
        {factor.bearish_signals.length > 0 && (
          <div>
            <Text type="danger" strong>
              <TrendingDownOutlined /> 看空信号：
            </Text>
            <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
              {factor.bearish_signals.map((signal, idx) => (
                <li key={idx}>
                  <Text type="danger">{signal.message}</Text>
                </li>
              ))}
            </ul>
          </div>
        )}
        {factor.bullish_signals.length === 0 && factor.bearish_signals.length === 0 && (
          <Text type="secondary">暂无信号</Text>
        )}
      </Space>
    </Card>
  );
};


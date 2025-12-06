import { useState } from 'react';
import { Button, Input, Form, Space, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { stockApi } from '../api/client';
import type { AnalysisReport } from '../types';

interface StockAnalysisFormProps {
  onAnalysisComplete: (reports: AnalysisReport[]) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const StockAnalysisForm: React.FC<StockAnalysisFormProps> = ({
  onAnalysisComplete,
  loading,
  setLoading,
}) => {
  const [form] = Form.useForm();

  const handleSubmit = async (values: { symbols: string }) => {
    const symbols = values.symbols
      .split(/[,，\s]+/)
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);

    if (symbols.length === 0) {
      message.error('请输入至少一个股票代码');
      return;
    }

    setLoading(true);
    try {
      const reports = await stockApi.analyzeStocks(symbols);
      if (reports.length === 0) {
        message.warning('未获取到任何股票数据，请检查股票代码是否正确');
      } else {
        message.success(`成功分析 ${reports.length} 只股票`);
        onAnalysisComplete(reports);
      }
    } catch (error: any) {
      console.error('分析失败:', error);
      message.error(error.response?.data?.detail || '分析失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form form={form} onFinish={handleSubmit} layout="inline" style={{ marginBottom: 24 }}>
      <Form.Item
        name="symbols"
        rules={[{ required: true, message: '请输入股票代码' }]}
        style={{ flex: 1, minWidth: 300 }}
      >
        <Input
          placeholder="输入股票代码，多个代码用逗号或空格分隔（如：NVDA, AAPL, 600519）"
          size="large"
          disabled={loading}
        />
      </Form.Item>
      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<SearchOutlined />}
          size="large"
          loading={loading}
        >
          分析
        </Button>
      </Form.Item>
    </Form>
  );
};


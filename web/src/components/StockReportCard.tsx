import { Card, Tag, Progress, Typography, Space, Divider, Empty, Button } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, UpOutlined, DownOutlined } from '@ant-design/icons'
import { useState } from 'react'
import type { AnalysisReport } from '../types'

const { Title, Text } = Typography

interface StockReportCardProps {
  report: AnalysisReport
}

export const StockReportCard: React.FC<StockReportCardProps> = ({ report }) => {
  const [expandedFactors, setExpandedFactors] = useState<Set<string>>(new Set())
  const [isStockExpanded, setIsStockExpanded] = useState(false)

  const getFearGreedColor = (index: number) => {
    if (index < 20) return { status: 'exception' as const, color: '#dc2626' }
    if (index < 40) return { status: 'exception' as const, color: '#f43f5e' }
    if (index < 60) return { status: 'active' as const, color: '#f59e0b' }
    if (index < 80) return { status: 'success' as const, color: '#34d399' }
    return { status: 'success' as const, color: '#10b981' }
  }

  const getEmojiFromLabel = (label: string) => {
    const emojiMatch = label.match(
      /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/u
    )
    return emojiMatch ? emojiMatch[0] : ''
  }

  const toggleFactor = (factorKey: string) => {
    setExpandedFactors(prev => {
      const newSet = new Set(prev)
      if (newSet.has(factorKey)) {
        newSet.delete(factorKey)
      } else {
        newSet.add(factorKey)
      }
      return newSet
    })
  }

  const toggleAllFactors = (factors: typeof report.factors, expand: boolean) => {
    setExpandedFactors(prev => {
      const newSet = new Set(prev)
      factors.forEach(factor => {
        const key = `${report.symbol}-${factor.key}`
        if (expand) {
          newSet.add(key)
        } else {
          newSet.delete(key)
        }
      })
      return newSet
    })
  }

  const technicalFactors = report.factors.filter(f => f.category === '技术面')
  const fundamentalFactors = report.factors.filter(f => f.category === '基本面')
  const fearGreedTheme = getFearGreedColor(report.fear_greed.index)
  const emoji = getEmojiFromLabel(report.fear_greed.label)
  const labelText = report.fear_greed.label
    .replace(
      /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]/gu,
      ''
    )
    .trim()

  return (
    <Card
      style={{ marginBottom: 24 }}
      title={
        <div
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}
          onClick={() => setIsStockExpanded(!isStockExpanded)}
        >
          {isStockExpanded ? <UpOutlined /> : <DownOutlined />}
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              {report.stock_name || report.symbol}
            </Title>
            <Tag color="blue">{report.symbol}</Tag>
            <Text strong style={{ color: '#1890ff', fontSize: 18 }}>
              ${report.price.toFixed(2)}
            </Text>
          </Space>
        </div>
      }
      extra={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 150 }}>
          <span style={{ fontSize: 16 }}>{emoji}</span>
          <Text strong style={{ color: fearGreedTheme.color, fontSize: 14 }}>
            {report.fear_greed.index.toFixed(1)}
          </Text>
          <Text style={{ fontSize: 12, color: '#666' }}>{labelText}</Text>
          <Progress
            type="line"
            percent={report.fear_greed.index}
            status={fearGreedTheme.status}
            strokeColor={fearGreedTheme.color}
            showInfo={false}
            style={{ width: 60 }}
          />
        </div>
      }
    >
      {isStockExpanded && (
        <>
          {/* 技术面因子 */}
          {technicalFactors.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 12,
                }}
              >
                <Divider orientation="left" style={{ margin: 0 }}>
                  <Text strong>技术面</Text>
                </Divider>
                <Button
                  size="small"
                  type="link"
                  onClick={() => {
                    const allExpanded = technicalFactors.every(f =>
                      expandedFactors.has(`${report.symbol}-${f.key}`)
                    )
                    toggleAllFactors(technicalFactors, !allExpanded)
                  }}
                >
                  {technicalFactors.every(f => expandedFactors.has(`${report.symbol}-${f.key}`))
                    ? '收起全部'
                    : '展开全部'}
                </Button>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                  gap: 12,
                }}
              >
                {technicalFactors.map(factor => (
                  <FactorItem
                    key={factor.key}
                    factor={factor}
                    stockSymbol={report.symbol}
                    isExpanded={expandedFactors.has(`${report.symbol}-${factor.key}`)}
                    onToggle={() => toggleFactor(`${report.symbol}-${factor.key}`)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 基本面因子 */}
          {fundamentalFactors.length > 0 && (
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 12,
                }}
              >
                <Divider orientation="left" style={{ margin: 0 }}>
                  <Text strong>基本面</Text>
                </Divider>
                <Button
                  size="small"
                  type="link"
                  onClick={() => {
                    const allExpanded = fundamentalFactors.every(f =>
                      expandedFactors.has(`${report.symbol}-${f.key}`)
                    )
                    toggleAllFactors(fundamentalFactors, !allExpanded)
                  }}
                >
                  {fundamentalFactors.every(f => expandedFactors.has(`${report.symbol}-${f.key}`))
                    ? '收起全部'
                    : '展开全部'}
                </Button>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                  gap: 12,
                }}
              >
                {fundamentalFactors.map(factor => (
                  <FactorItem
                    key={factor.key}
                    factor={factor}
                    stockSymbol={report.symbol}
                    isExpanded={expandedFactors.has(`${report.symbol}-${factor.key}`)}
                    onToggle={() => toggleFactor(`${report.symbol}-${factor.key}`)}
                  />
                ))}
              </div>
            </div>
          )}

          {technicalFactors.length === 0 && fundamentalFactors.length === 0 && (
            <Empty description="暂无因子数据" size="small" />
          )}
        </>
      )}
    </Card>
  )
}

interface FactorItemProps {
  factor: {
    key: string
    name: string
    status: string
    bullish_signals: Array<{ factor: string; message: string }>
    bearish_signals: Array<{ factor: string; message: string }>
  }
  stockSymbol: string
  isExpanded: boolean
  onToggle: () => void
}

const FactorItem: React.FC<FactorItemProps> = ({ factor, isExpanded, onToggle }) => {
  const getFactorStatus = (factor: FactorItemProps['factor']) => {
    const bullishCount = factor.bullish_signals.length
    const bearishCount = factor.bearish_signals.length
    if (bullishCount > bearishCount) return 'bullish'
    if (bearishCount > bullishCount) return 'bearish'
    return 'neutral'
  }

  const status = getFactorStatus(factor)
  const statusColor = status === 'bullish' ? 'success' : status === 'bearish' ? 'error' : 'warning'
  const statusStyle =
    status === 'bullish'
      ? { bg: '#f0fdf4', border: '#86efac', text: '#166534' }
      : status === 'bearish'
        ? { bg: '#fef2f2', border: '#fca5a5', text: '#991b1b' }
        : { bg: '#fffbeb', border: '#fcd34d', text: '#92400e' }

  return (
    <Card
      size="small"
      style={{
        marginBottom: 0,
        backgroundColor: isExpanded ? statusStyle.bg : undefined,
        borderColor: isExpanded ? statusStyle.border : undefined,
        cursor: 'pointer',
      }}
      title={
        <div
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
          onClick={onToggle}
        >
          <Space>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor:
                  status === 'bullish' ? '#10b981' : status === 'bearish' ? '#ef4444' : '#f59e0b',
              }}
            />
            <Text strong>{factor.name}</Text>
            <Tag color={statusColor} style={{ fontSize: 11 }}>
              {factor.status || '-'}
            </Tag>
          </Space>
          {isExpanded ? <UpOutlined /> : <DownOutlined />}
        </div>
      }
      onClick={onToggle}
    >
      {isExpanded && (
        <div style={{ paddingTop: 8 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            {factor.bullish_signals.length > 0 && (
              <div>
                <Text
                  type="success"
                  strong
                  style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  <ArrowUpOutlined /> 看涨信号：
                </Text>
                <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                  {factor.bullish_signals.map((signal, idx) => (
                    <li key={idx}>
                      <Text type="success" style={{ fontSize: 12 }}>
                        {signal.message}
                      </Text>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {factor.bearish_signals.length > 0 && (
              <div>
                <Text
                  type="danger"
                  strong
                  style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  <ArrowDownOutlined /> 看跌信号：
                </Text>
                <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                  {factor.bearish_signals.map((signal, idx) => (
                    <li key={idx}>
                      <Text type="danger" style={{ fontSize: 12 }}>
                        {signal.message}
                      </Text>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {factor.bullish_signals.length === 0 && factor.bearish_signals.length === 0 && (
              <Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>
                暂无信号
              </Text>
            )}
          </Space>
        </div>
      )}
    </Card>
  )
}

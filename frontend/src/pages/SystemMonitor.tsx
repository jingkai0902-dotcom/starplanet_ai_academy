/**
 * 系统监控仪表盘页面
 * 显示系统状态、性能监控、数据库统计等
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Table,
  message,
  Spin,
  Flex,
  Alert,
  Badge,
  Switch,
  Button,
  Space,
} from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  UserOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
const Line = (_props: any) => null;
const Gauge = (_props: any) => null;
import { useResponsive } from '../hooks/useResponsive';
import {
  getDashboardOverview,
  getSystemStatus,
  getDatabaseStats,
  getPerformanceStats,
  formatBytes,
  getHealthColor,
  type DashboardOverview,
  type SystemStatus,
  type DatabaseStats,
  type PerformanceStats
} from '../services/monitorService';

const { Title, Text } = Typography;

// 计算系统健康评分
const calculateHealthScore = (
  cpuPercent: number,
  memoryPercent: number,
  diskPercent: number,
  apiErrorRate: number
): number => {
  let score = 100;

  // CPU使用率扣分（>50%开始扣分）
  if (cpuPercent > 50) score -= (cpuPercent - 50) * 0.5;

  // 内存使用率扣分（>60%开始扣分）
  if (memoryPercent > 60) score -= (memoryPercent - 60) * 0.7;

  // 磁盘使用率扣分（>70%开始扣分）
  if (diskPercent > 70) score -= (diskPercent - 70) * 0.5;

  // API错误率扣分
  if (apiErrorRate > 1) score -= apiErrorRate * 5;

  return Math.max(0, Math.min(100, score));
};

// 获取健康评分等级
const getHealthLevel = (score: number): { text: string; color: string } => {
  if (score >= 90) return { text: '优秀', color: '#52c41a' };
  if (score >= 75) return { text: '良好', color: '#1890ff' };
  if (score >= 60) return { text: '一般', color: '#faad14' };
  if (score >= 40) return { text: '较差', color: '#ff7a45' };
  return { text: '危险', color: '#ff4d4f' };
};

const SystemMonitor: React.FC = () => {
  const { isMobile, spacing } = useResponsive();

  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [dbStats, setDbStats] = useState<DatabaseStats | null>(null);
  const [perfStats, setPerfStats] = useState<PerformanceStats | null>(null);

  // 自动刷新开关
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 告警状态
  const [alerts, setAlerts] = useState<{ type: 'warning' | 'error'; message: string }[]>([]);

  useEffect(() => {
    loadDashboardData();

    // 自动刷新
    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const loadDashboardData = async () => {
    try {
      const [overviewData, systemData, dbData, perfData] = await Promise.all([
        getDashboardOverview(),
        getSystemStatus(),
        getDatabaseStats(),
        getPerformanceStats()
      ]);

      setOverview(overviewData);
      setSystemStatus(systemData);
      setDbStats(dbData);
      setPerfStats(perfData);

      // 检查告警
      checkAlerts(overviewData, systemData, perfData);
    } catch (error: any) {
      if (error.response?.status === 403) {
        message.error('需要管理员权限才能访问此页面');
      } else {
        message.error('加载失败：' + (error.response?.data?.error || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 告警检测
  const checkAlerts = (
    overviewData: DashboardOverview,
    systemData: SystemStatus,
    perfData: PerformanceStats
  ) => {
    const newAlerts: { type: 'warning' | 'error'; message: string }[] = [];

    // CPU告警
    if (systemData.cpu.percent > 90) {
      newAlerts.push({ type: 'error', message: `CPU使用率过高：${systemData.cpu.percent.toFixed(1)}%` });
    } else if (systemData.cpu.percent > 80) {
      newAlerts.push({ type: 'warning', message: `CPU使用率较高：${systemData.cpu.percent.toFixed(1)}%` });
    }

    // 内存告警
    if (systemData.memory.percent > 90) {
      newAlerts.push({ type: 'error', message: `内存使用率过高：${systemData.memory.percent.toFixed(1)}%` });
    } else if (systemData.memory.percent > 80) {
      newAlerts.push({ type: 'warning', message: `内存使用率较高：${systemData.memory.percent.toFixed(1)}%` });
    }

    // 磁盘告警
    if (systemData.disk.percent > 90) {
      newAlerts.push({ type: 'error', message: `磁盘使用率过高：${systemData.disk.percent.toFixed(1)}%` });
    } else if (systemData.disk.percent > 80) {
      newAlerts.push({ type: 'warning', message: `磁盘使用率较高：${systemData.disk.percent.toFixed(1)}%` });
    }

    // API错误率告警
    const avgErrorRate = Object.values(perfData.endpoint_stats || {})
      .reduce((sum, stat) => sum + stat.error_rate, 0) / Object.keys(perfData.endpoint_stats || {}).length;

    if (avgErrorRate > 10) {
      newAlerts.push({ type: 'error', message: `API平均错误率过高：${avgErrorRate.toFixed(1)}%` });
    } else if (avgErrorRate > 5) {
      newAlerts.push({ type: 'warning', message: `API平均错误率较高：${avgErrorRate.toFixed(1)}%` });
    }

    setAlerts(newAlerts);
  };

  // 计算系统健康评分
  const calculateScore = () => {
    if (!overview || !systemStatus || !perfStats) return 0;

    const avgErrorRate = Object.values(perfStats.endpoint_stats || {})
      .reduce((sum, stat) => sum + stat.error_rate, 0) / Object.keys(perfStats.endpoint_stats || {}).length || 0;

    return calculateHealthScore(
      systemStatus.cpu.percent,
      systemStatus.memory.percent,
      systemStatus.disk.percent,
      avgErrorRate
    );
  };

  const healthScore = calculateScore();
  const healthLevel = getHealthLevel(healthScore);

  if (loading && !overview) {
    return (
      <Flex justify="center" align="center" style={{ minHeight: '60vh' }}>
        <Spin size="large" tip="正在加载系统监控..." />
      </Flex>
    );
  }

  // 准备活动趋势图表数据
  const activityChartData = overview?.activity_trend.map(item => ({
    date: item.date,
    value: item.sessions
  })) || [];

  const activityChartConfig = {
    data: activityChartData,
    xField: 'date',
    yField: 'value',
    smooth: true,
    color: '#1890ff',
    point: {
      size: 3,
      shape: 'circle'
    },
    label: {
      style: {
        fill: '#666'
      }
    },
    xAxis: {
      title: {
        text: '日期'
      }
    },
    yAxis: {
      title: {
        text: '训练次数'
      }
    }
  };

  // 准备性能统计表格数据
  const perfTableData = Object.entries(perfStats?.endpoint_stats || {})
    .map(([endpoint, stats]) => ({
      key: endpoint,
      endpoint,
      ...stats
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const perfTableColumns = [
    {
      title: '端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true,
      width: isMobile ? 150 : undefined
    },
    {
      title: '请求数',
      dataIndex: 'count',
      key: 'count',
      sorter: (a: any, b: any) => a.count - b.count
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_time',
      key: 'avg_time',
      render: (time: number) => `${(time * 1000).toFixed(0)}ms`,
      sorter: (a: any, b: any) => a.avg_time - b.avg_time
    },
    {
      title: '错误率',
      dataIndex: 'error_rate',
      key: 'error_rate',
      render: (rate: number) => (
        <Tag color={rate > 5 ? 'red' : rate > 1 ? 'orange' : 'green'}>
          {rate.toFixed(1)}%
        </Tag>
      ),
      sorter: (a: any, b: any) => a.error_rate - b.error_rate
    }
  ];

  return (
    <div style={{ padding: spacing.page }}>
      {/* Header */}
      <Flex justify="space-between" align="center" style={{ marginBottom: spacing.section }} wrap="wrap" gap={spacing.small}>
        <Flex align="center" gap={spacing.small}>
          <DashboardOutlined style={{ fontSize: isMobile ? '32px' : '40px', color: '#1890ff' }} />
          <Title level={isMobile ? 3 : 2} style={{ margin: 0 }}>系统监控</Title>
        </Flex>

        <Space>
          <span style={{ fontSize: 14 }}>自动刷新(30秒):</span>
          <Switch checked={autoRefresh} onChange={setAutoRefresh} />
          <Button icon={<ReloadOutlined />} onClick={loadDashboardData}>
            刷新
          </Button>
        </Space>
      </Flex>

      {/* 告警信息 */}
      {alerts.length > 0 && (
        <Alert
          type={alerts.some(a => a.type === 'error') ? 'error' : 'warning'}
          message={`系统告警 (${alerts.length})`}
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {alerts.map((alert, index) => (
                <li key={index}>
                  {alert.type === 'error' ? <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} /> : <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />}
                  {alert.message}
                </li>
              ))}
            </ul>
          }
          showIcon
          closable
          style={{ marginBottom: spacing.section }}
        />
      )}

      {/* 系统健康评分 */}
      {systemStatus && (
        <Card style={{ marginBottom: spacing.section }}>
          <Row gutter={[spacing.medium, spacing.medium]}>
            <Col xs={24} md={12}>
              <Flex vertical align="center">
                <Title level={4}>系统健康评分</Title>
                <Gauge
                  percent={healthScore / 100}
                  range={{
                    color: healthLevel.color,
                  }}
                  indicator={{
                    pointer: {
                      style: {
                        stroke: healthLevel.color,
                      },
                    },
                    pin: {
                      style: {
                        stroke: healthLevel.color,
                      },
                    },
                  }}
                  statistic={{
                    content: {
                      style: {
                        fontSize: '36px',
                        color: healthLevel.color,
                      },
                      formatter: () => `${healthScore.toFixed(0)}`,
                    },
                  }}
                  height={200}
                />
                <Tag color={healthLevel.color} style={{ fontSize: 16, marginTop: 12 }}>
                  {healthLevel.text}
                </Tag>
              </Flex>
            </Col>
            <Col xs={24} md={12}>
              <Title level={5}>评分说明</Title>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Flex justify="space-between">
                  <Text>CPU使用率:</Text>
                  <Text strong>{systemStatus.cpu.percent.toFixed(1)}%</Text>
                </Flex>
                <Flex justify="space-between">
                  <Text>内存使用率:</Text>
                  <Text strong>{systemStatus.memory.percent.toFixed(1)}%</Text>
                </Flex>
                <Flex justify="space-between">
                  <Text>磁盘使用率:</Text>
                  <Text strong>{systemStatus.disk.percent.toFixed(1)}%</Text>
                </Flex>
                <Flex justify="space-between">
                  <Text>API错误率:</Text>
                  <Text strong>
                    {(Object.values(perfStats?.endpoint_stats || {})
                      .reduce((sum, stat) => sum + stat.error_rate, 0) / Object.keys(perfStats?.endpoint_stats || {}).length || 0
                    ).toFixed(2)}%
                  </Text>
                </Flex>
                <Alert
                  message="健康评分综合考虑CPU、内存、磁盘使用率和API错误率"
                  type="info"
                  showIcon
                  style={{ marginTop: 12 }}
                />
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* 关键指标卡片 */}
      {overview && (
        <>
          <Row gutter={[spacing.medium, spacing.medium]} style={{ marginBottom: spacing.section }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="总用户数"
                  value={overview.users.total}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                  suffix={
                    <Text type="secondary" style={{ fontSize: '14px' }}>
                      (+{overview.users.new_7d})
                    </Text>
                  }
                />
                <Text type="secondary">增长率: {overview.users.growth_rate}%</Text>
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="总训练次数"
                  value={overview.sessions.total}
                  prefix={<TrophyOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
                <Text type="secondary">今日: {overview.sessions.today} 次</Text>
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="CPU使用率"
                  value={overview.system.cpu_percent}
                  suffix="%"
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ color: getHealthColor(overview.system.cpu_percent) }}
                />
                <Progress
                  percent={overview.system.cpu_percent}
                  strokeColor={getHealthColor(overview.system.cpu_percent)}
                  showInfo={false}
                  size="small"
                />
                {overview.system.cpu_percent > 80 && (
                  <Tag color="warning" icon={<WarningOutlined />} style={{ marginTop: 8 }}>
                    使用率过高
                  </Tag>
                )}
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="内存使用率"
                  value={overview.system.memory_percent}
                  suffix="%"
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ color: getHealthColor(overview.system.memory_percent) }}
                />
                <Progress
                  percent={overview.system.memory_percent}
                  strokeColor={getHealthColor(overview.system.memory_percent)}
                  showInfo={false}
                  size="small"
                />
                {overview.system.memory_percent > 80 && (
                  <Tag color="warning" icon={<WarningOutlined />} style={{ marginTop: 8 }}>
                    使用率过高
                  </Tag>
                )}
              </Card>
            </Col>
          </Row>

          {/* 活动趋势图 */}
          <Card
            title="7天活动趋势"
            style={{ marginBottom: spacing.section }}
          >
            <Line {...activityChartConfig} height={250} />
          </Card>
        </>
      )}

      {/* 系统资源详情 */}
      {systemStatus && (
        <Card
          title={
            <Flex align="center" gap={spacing.small}>
              <DatabaseOutlined />
              <span>系统资源详情</span>
            </Flex>
          }
          style={{ marginBottom: spacing.section }}
        >
          <Row gutter={[spacing.medium, spacing.medium]}>
            <Col xs={24} md={8}>
              <Card size="small" title="CPU">
                <Statistic
                  title="使用率"
                  value={systemStatus.cpu.percent}
                  suffix="%"
                  precision={1}
                />
                <Text type="secondary">核心数: {systemStatus.cpu.count}</Text>
              </Card>
            </Col>

            <Col xs={24} md={8}>
              <Card size="small" title="内存">
                <Statistic
                  title="已使用"
                  value={formatBytes(systemStatus.memory.used)}
                />
                <Text type="secondary">
                  总计: {formatBytes(systemStatus.memory.total)}
                </Text>
                <Progress
                  percent={systemStatus.memory.percent}
                  strokeColor={getHealthColor(systemStatus.memory.percent)}
                  size="small"
                  style={{ marginTop: spacing.small }}
                />
              </Card>
            </Col>

            <Col xs={24} md={8}>
              <Card size="small" title="磁盘">
                <Statistic
                  title="已使用"
                  value={formatBytes(systemStatus.disk.used)}
                />
                <Text type="secondary">
                  总计: {formatBytes(systemStatus.disk.total)}
                </Text>
                <Progress
                  percent={systemStatus.disk.percent}
                  strokeColor={getHealthColor(systemStatus.disk.percent)}
                  size="small"
                  style={{ marginTop: spacing.small }}
                />
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* 数据库统计 */}
      {dbStats && (
        <Card
          title="数据库统计"
          style={{ marginBottom: spacing.section }}
        >
          <Row gutter={[spacing.medium, spacing.medium]}>
            <Col xs={24} sm={12} lg={8}>
              <Statistic
                title="活跃用户（7天）"
                value={dbStats.users.active_7d}
                suffix={`/ ${dbStats.users.total}`}
                prefix={<UserOutlined />}
              />
            </Col>

            <Col xs={24} sm={12} lg={8}>
              <Statistic
                title="会话完成率"
                value={dbStats.sessions.completion_rate}
                suffix="%"
                prefix={<TrophyOutlined />}
                precision={1}
              />
            </Col>

            <Col xs={24} sm={12} lg={8}>
              <Statistic
                title="24小时活动"
                value={dbStats.sessions.recent_24h}
                suffix="次"
                prefix={<ClockCircleOutlined />}
              />
            </Col>

            <Col xs={24} sm={12} lg={8}>
              <Statistic
                title="学习笔记"
                value={dbStats.content.notes}
                suffix="篇"
              />
            </Col>

            <Col xs={24} sm={12} lg={8}>
              <Statistic
                title="总积分"
                value={dbStats.content.total_points}
              />
            </Col>

            <Col xs={24} sm={12} lg={8}>
              <Statistic
                title="已颁发徽章"
                value={dbStats.content.badges_earned}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* API性能统计 */}
      {perfStats && (
        <Card
          title={
            <Flex align="center" gap={spacing.small}>
              <ThunderboltOutlined />
              <span>API性能统计（Top 10）</span>
              <Badge count={perfStats.total_requests} overflowCount={9999} />
            </Flex>
          }
        >
          <Table
            dataSource={perfTableData}
            columns={perfTableColumns}
            pagination={false}
            scroll={{ x: isMobile ? 600 : undefined }}
            size="small"
          />
        </Card>
      )}
    </div>
  );
};

export default SystemMonitor;

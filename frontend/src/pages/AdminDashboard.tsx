/**
 * 管理员数据分析面板
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Statistic,
  Row,
  Col,
  Button,
  Table,
  Tag,
  Space,
  Select,
  DatePicker,
  InputNumber,
  Skeleton,
  message,
  Flex,
} from 'antd';
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UserOutlined,
  BookOutlined,
  CheckCircleOutlined,
  StarOutlined,
  SyncOutlined,
} from '@ant-design/icons';
const Column = (_props: any) => null;
const Line = (_props: any) => null;
import {
  getAdminDashboard,
  type AdminOverview,
  type EmployeeData,
} from '../services/adminService';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();

  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [employees, setEmployees] = useState<EmployeeData[]>([]);
  const [filteredEmployees, setFilteredEmployees] = useState<EmployeeData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // 高级筛选状态
  const [filterPosition, setFilterPosition] = useState<string | null>(null);
  const [filterScoreRange, setFilterScoreRange] = useState<[number | null, number | null]>([null, null]);
  const [filterDateRange, setFilterDateRange] = useState<[Dayjs | null, Dayjs | null]>([null, null]);
  const [filterRetraining, setFilterRetraining] = useState<boolean>(false);

  // 加载数据
  const loadData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const data = await getAdminDashboard();
      if (data.success) {
        setOverview(data.overview);
        setEmployees(data.employees);
      } else {
        setError('获取数据失败');
      }
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('您没有管理员权限');
        message.error('您没有管理员权限');
      } else {
        setError(err.response?.data?.error || '网络错误');
        message.error(err.response?.data?.error || '网络错误');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 初始加载和自动刷新（30秒）
  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // 筛选逻辑
  useEffect(() => {
    let result = [...employees];

    // 按岗位筛选
    if (filterPosition) {
      result = result.filter((emp) => emp.position === filterPosition);
    }

    // 按分数区间筛选
    if (filterScoreRange[0] !== null) {
      result = result.filter((emp) => (emp.best_score || 0) >= filterScoreRange[0]!);
    }
    if (filterScoreRange[1] !== null) {
      result = result.filter((emp) => (emp.best_score || 0) <= filterScoreRange[1]!);
    }

    // 按复训状态筛选
    if (filterRetraining) {
      result = result.filter((emp) => emp.needs_retraining);
    }

    setFilteredEmployees(result);
  }, [employees, filterPosition, filterScoreRange, filterRetraining]);

  // 手动刷新
  const handleRefresh = () => {
    message.loading('刷新中...');
    loadData();
  };

  // 重置筛选
  const handleResetFilters = () => {
    setFilterPosition(null);
    setFilterScoreRange([null, null]);
    setFilterDateRange([null, null]);
    setFilterRetraining(false);
    message.success('已重置筛选条件');
  };

  // 数据导出（CSV格式）
  const handleExport = () => {
    if (filteredEmployees.length === 0) {
      message.warning('暂无数据可导出');
      return;
    }

    const headers = [
      '姓名',
      '岗位',
      '平均进度(%)',
      '最高分',
      '完成次数',
      '总次数',
      '距上次学习(天)',
      '积分',
      '状态',
    ];

    const rows = filteredEmployees.map((emp) => [
      emp.username,
      emp.position === 'sales' ? '销售' : '教师',
      emp.avg_progress,
      emp.best_score || '--',
      emp.completed_sessions,
      emp.total_sessions,
      emp.days_since_practice !== null ? emp.days_since_practice : '从未学习',
      emp.points,
      emp.needs_retraining ? '需要复训' : '正常',
    ]);

    const csvContent = [headers, ...rows]
      .map((row) => row.map((cell) => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `员工学习报表_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    message.success(`成功导出 ${filteredEmployees.length} 条数据`);
  };

  // 表格列定义
  const columns: ColumnsType<EmployeeData> = [
    {
      title: '姓名',
      dataIndex: 'username',
      key: 'username',
      fixed: 'left',
      width: 120,
      sorter: (a, b) => a.username.localeCompare(b.username),
    },
    {
      title: '岗位',
      dataIndex: 'position',
      key: 'position',
      width: 100,
      render: (position: string) => (
        <Tag color={position === 'sales' ? 'blue' : 'green'}>
          {position === 'sales' ? '销售' : '教师'}
        </Tag>
      ),
      filters: [
        { text: '销售', value: 'sales' },
        { text: '教师', value: 'teacher' },
      ],
      onFilter: (value, record) => record.position === value,
    },
    {
      title: '平均进度',
      dataIndex: 'avg_progress',
      key: 'avg_progress',
      width: 120,
      sorter: (a, b) => a.avg_progress - b.avg_progress,
      render: (progress: number) => {
        let color = '#ef4444';
        if (progress >= 80) color = '#10b981';
        else if (progress >= 60) color = '#f59e0b';

        return (
          <div style={{ width: '100%' }}>
            <div
              style={{
                height: 8,
                background: '#f0f0f0',
                borderRadius: 4,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${progress}%`,
                  height: '100%',
                  background: color,
                  transition: 'width 0.3s',
                }}
              />
            </div>
            <div style={{ fontSize: 12, marginTop: 4, textAlign: 'center' }}>
              {progress}%
            </div>
          </div>
        );
      },
    },
    {
      title: '最高分',
      dataIndex: 'best_score',
      key: 'best_score',
      width: 100,
      sorter: (a, b) => (a.best_score || 0) - (b.best_score || 0),
      render: (score: number | null) => {
        if (!score) return <span style={{ color: '#999' }}>--</span>;

        let color = '#ef4444';
        if (score >= 80) color = '#10b981';
        else if (score >= 60) color = '#f59e0b';

        return <span style={{ color, fontWeight: 600, fontSize: 16 }}>{score}</span>;
      },
    },
    {
      title: '完成次数',
      dataIndex: 'completed_sessions',
      key: 'completed_sessions',
      width: 120,
      sorter: (a, b) => a.completed_sessions - b.completed_sessions,
      render: (completed: number, record) => (
        <span>
          {completed} / {record.total_sessions}
        </span>
      ),
    },
    {
      title: '距上次学习',
      dataIndex: 'days_since_practice',
      key: 'days_since_practice',
      width: 120,
      sorter: (a, b) =>
        (a.days_since_practice || 9999) - (b.days_since_practice || 9999),
      render: (days: number | null) => {
        if (days === null) return <span style={{ color: '#999' }}>从未学习</span>;
        if (days > 7) return <span style={{ color: '#ef4444' }}>{days} 天</span>;
        if (days > 3) return <span style={{ color: '#f59e0b' }}>{days} 天</span>;
        return <span style={{ color: '#10b981' }}>{days} 天</span>;
      },
    },
    {
      title: '积分',
      dataIndex: 'points',
      key: 'points',
      width: 100,
      sorter: (a, b) => a.points - b.points,
      render: (points: number) => (
        <span style={{ color: '#f59e0b', fontWeight: 600 }}>{points}</span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'needs_retraining',
      key: 'needs_retraining',
      width: 100,
      fixed: 'right',
      render: (needs: boolean) =>
        needs ? (
          <Tag color="error">需要复训</Tag>
        ) : (
          <Tag color="success">正常</Tag>
        ),
      filters: [
        { text: '需要复训', value: true },
        { text: '正常', value: false },
      ],
      onFilter: (value, record) => record.needs_retraining === value,
    },
  ];

  // 图表配置 - 员工平均分分布（柱状图）
  const scoreDistributionConfig = {
    data: employees.map((emp) => ({
      name: emp.username,
      score: emp.best_score || 0,
      position: emp.position === 'sales' ? '销售' : '教师',
    })),
    xField: 'name',
    yField: 'score',
    seriesField: 'position',
    color: ['#1890ff', '#52c41a'],
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
    label: {
      position: 'top' as const,
      style: {
        fill: '#000',
        opacity: 0.6,
      },
    },
    xAxis: {
      label: {
        autoRotate: true,
        autoHide: true,
      },
    },
    legend: {
      position: 'top-right' as const,
    },
  };

  // 图表配置 - 完成趋势（折线图）
  const completionTrendConfig = {
    data: employees.map((emp) => ({
      name: emp.username,
      completed: emp.completed_sessions,
      total: emp.total_sessions,
    })),
    xField: 'name',
    yField: 'completed',
    smooth: true,
    point: {
      size: 5,
      shape: 'diamond',
    },
    label: {
      style: {
        fill: '#aaa',
      },
    },
  };

  if (isLoading) {
    return (
      <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
        <Card>
          <Skeleton active paragraph={{ rows: 2 }} />
        </Card>
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <Col key={i} xs={24} sm={12} lg={8} xl={4.8}>
              <Card>
                <Skeleton active paragraph={{ rows: 1 }} />
              </Card>
            </Col>
          ))}
        </Row>
        <Card style={{ marginTop: 16 }}>
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
        <Card>
          <Flex vertical align="center" gap="middle" style={{ padding: '60px 20px' }}>
            <div style={{ fontSize: 64 }}>⚠️</div>
            <h2 style={{ color: '#ff4d4f' }}>{error}</h2>
            <Button type="primary" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
              返回主页
            </Button>
          </Flex>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 头部 */}
      <Card style={{ marginBottom: 16 }}>
        <Flex justify="space-between" align="center" wrap="wrap" gap="middle">
          <Flex align="center" gap="middle">
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
              返回
            </Button>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>
              📊 管理员数据分析面板
            </h1>
          </Flex>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
              刷新
            </Button>
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
              导出数据
            </Button>
          </Space>
        </Flex>
      </Card>

      {/* 概览卡片 */}
      {overview && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} lg={8} xl={4.8}>
            <Card>
              <Statistic
                title="总员工数"
                value={overview.total_employees}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={4.8}>
            <Card>
              <Statistic
                title="总学习次数"
                value={overview.total_sessions}
                prefix={<BookOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={4.8}>
            <Card>
              <Statistic
                title="完成率"
                value={overview.completion_rate}
                suffix="%"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={4.8}>
            <Card>
              <Statistic
                title="平均分"
                value={overview.average_score}
                prefix={<StarOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={4.8}>
            <Card>
              <Statistic
                title="复训率"
                value={overview.retraining_rate}
                suffix="%"
                prefix={<SyncOutlined />}
                valueStyle={{ color: '#eb2f96' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 高级筛选 */}
      <Card title="高级筛选" style={{ marginBottom: 16 }}>
        <Flex vertical gap="middle">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <div>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>岗位</div>
                <Select
                  style={{ width: '100%' }}
                  placeholder="选择岗位"
                  allowClear
                  value={filterPosition}
                  onChange={setFilterPosition}
                  options={[
                    { label: '销售', value: 'sales' },
                    { label: '教师', value: 'teacher' },
                  ]}
                />
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>最低分</div>
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={100}
                  placeholder="最低分"
                  value={filterScoreRange[0]}
                  onChange={(val) => setFilterScoreRange([val, filterScoreRange[1]])}
                />
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>最高分</div>
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={100}
                  placeholder="最高分"
                  value={filterScoreRange[1]}
                  onChange={(val) => setFilterScoreRange([filterScoreRange[0], val])}
                />
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>复训状态</div>
                <Select
                  style={{ width: '100%' }}
                  placeholder="选择状态"
                  allowClear
                  value={filterRetraining}
                  onChange={setFilterRetraining}
                  options={[
                    { label: '仅需要复训', value: true },
                    { label: '全部', value: false },
                  ]}
                />
              </div>
            </Col>
          </Row>
          <Button onClick={handleResetFilters}>重置筛选</Button>
        </Flex>
      </Card>

      {/* 数据表格 */}
      <Card
        title={`员工学习情况 (${filteredEmployees.length} / ${employees.length})`}
        style={{ marginBottom: 16 }}
      >
        <Table
          columns={columns}
          dataSource={filteredEmployees}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          rowClassName={(record) => (record.needs_retraining ? 'needs-retraining-row' : '')}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 图表可视化 */}
      {employees.length > 0 && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="员工分数分布">
              <Column {...scoreDistributionConfig} height={300} />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="完成次数统计">
              <Line {...completionTrendConfig} height={300} />
            </Card>
          </Col>
        </Row>
      )}

      <style>{`
        .needs-retraining-row {
          background: #fff1f0 !important;
        }
        .needs-retraining-row:hover {
          background: #ffccc7 !important;
        }
      `}</style>
    </div>
  );
};

export default AdminDashboard;

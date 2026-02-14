import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Space,
  Typography,
  Tag,
  Spin,
  Progress,
  Divider,
  Row,
  Col,
  Statistic,
  message,
  Empty,
  List,
  Alert,
  Segmented,
} from 'antd';
import {
  ArrowLeftOutlined,
  TrophyOutlined,
  RiseOutlined,
  LineChartOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  BulbOutlined,
  FireOutlined,
} from '@ant-design/icons';
const toChartNumber = (v: any): number => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

const Line = (props: any) => {
  const data = Array.isArray(props?.data) ? props.data.slice(0, 80) : [];
  const yField = props?.yField || 'y';
  const w = 700;
  const h = props?.height || 260;

  if (data.length === 0) {
    return <div style={{ height: h, color: '#999', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>暂无数据</div>;
  }

  const ys = data.map((d: any) => toChartNumber(d?.[yField]));
  const min = Math.min(...ys, 0);
  const max = Math.max(...ys, 1);
  const range = max - min || 1;
  const left = 14;
  const top = 12;
  const plotW = w - 28;
  const plotH = h - 24;

  const points = ys.map((y, i) => {
    const x = left + (i / Math.max(ys.length - 1, 1)) * plotW;
    const py = top + (1 - (y - min) / range) * plotH;
    return `${x},${py}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: h }}>
      <polyline fill="none" stroke="#1677ff" strokeWidth="2" points={points} />
    </svg>
  );
};
import { getCoachingEffectReport, getLearningCurve } from '../services/trainingService';
import { useAuthStore } from '../stores/authStore';
import type { CoachingEffectReport, LearningCurveData } from '../types/training';

const { Title, Text, Paragraph } = Typography;

const CoachingEffectAnalysis = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [report, setReport] = useState<CoachingEffectReport | null>(null);
  const [curveData, setCurveData] = useState<LearningCurveData | null>(null);
  const [loading, setLoading] = useState(true);
  const [curveDays, setCurveDays] = useState<number>(30);

  useEffect(() => {
    const loadData = async () => {
      if (!user?.id) {
        message.error('请先登录');
        navigate('/login');
        return;
      }

      try {
        // 并行请求两个API
        const [reportRes, curveRes] = await Promise.all([
          getCoachingEffectReport(user.id),
          getLearningCurve(user.id, curveDays),
        ]);

        if (reportRes.success) {
          setReport(reportRes.report);
        } else {
          message.warning(reportRes.message || '暂无辅导数据');
        }

        if (curveRes.success) {
          setCurveData(curveRes.curve_data);
        }
      } catch (error: any) {
        console.error('加载失败:', error);
        message.error(error.message || '加载数据失败');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user, navigate, curveDays]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!report || !report.has_data) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Empty description="暂无辅导数据，完成苏格拉底辅导后即可查看效果分析" />
        <Button type="primary" onClick={() => navigate('/training')} style={{ marginTop: 16 }}>
          开始训练
        </Button>
      </div>
    );
  }

  // 层级名称映射
  const levelNameMap: Record<string, string> = {
    awareness: '觉察层',
    analysis: '分析层',
    strategy: '策略层',
    action: '行动层',
  };

  // 效果等级颜色
  const getEffectivenessColor = (effectiveness: string) => {
    switch (effectiveness) {
      case 'excellent': return 'success';
      case 'good': return 'processing';
      case 'moderate': return 'warning';
      case 'poor': return 'error';
      default: return 'default';
    }
  };

  // 效果等级文本
  const effectivenessTextMap: Record<string, string> = {
    excellent: '优秀',
    good: '良好',
    moderate: '中等',
    poor: '较差',
  };

  // 准备学习曲线图表数据
  const chartData = curveData && curveData.has_data ? [
    ...(curveData.dates?.map((date, index) => ({
      date,
      score: curveData.scores_before![index],
      type: '辅导前',
    })) || []),
    ...(curveData.dates?.map((date, index) => ({
      date,
      score: curveData.scores_after![index],
      type: '辅导后',
    })) || []),
  ] : [];

  const chartConfig = {
    data: chartData,
    xField: 'date',
    yField: 'score',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: ['#ff7875', '#52c41a'],
    yAxis: {
      min: 0,
      max: 100,
    },
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      showMarkers: true,
    },
  };

  return (
    <div style={{ width: '100%', padding: '20px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header */}
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/training')}
            >
              返回训练列表
            </Button>
            <Tag color="purple" icon={<LineChartOutlined />}>
              辅导效果分析
            </Tag>
          </Space>
        </Card>

        {/* Overall Statistics */}
        <Card
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
          }}
        >
          <Space direction="vertical" size="middle" style={{ width: '100%', textAlign: 'center' }}>
            <TrophyOutlined style={{ fontSize: '48px', color: '#ffd700' }} />
            <Title level={2} style={{ margin: 0, color: 'white' }}>
              辅导效果总览
            </Title>
            <Row gutter={[16, 16]} style={{ width: '100%' }}>
              <Col span={6}>
                <Statistic
                  title={<span style={{ color: 'white' }}>总辅导次数</span>}
                  value={report.summary?.total_coaching_sessions || 0}
                  suffix="次"
                  valueStyle={{ color: 'white' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title={<span style={{ color: 'white' }}>完成辅导</span>}
                  value={report.summary?.completed_coaching_sessions || 0}
                  suffix="次"
                  valueStyle={{ color: 'white' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title={<span style={{ color: 'white' }}>完成率</span>}
                  value={report.completion_rate || 0}
                  suffix="%"
                  valueStyle={{ color: 'white' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title={<span style={{ color: 'white' }}>平均提升</span>}
                  value={report.summary?.avg_improvement.toFixed(1) || 0}
                  suffix="分"
                  valueStyle={{ color: 'white' }}
                  prefix={<RiseOutlined />}
                />
              </Col>
            </Row>
          </Space>
        </Card>

        {/* Quality Improvement */}
        <Card title={<><RiseOutlined /> 质量提升对比</>}>
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Statistic
                title="辅导前平均分"
                value={report.summary?.avg_score_before.toFixed(1) || 0}
                suffix="分"
                valueStyle={{ color: '#ff7875' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="辅导后平均分"
                value={report.summary?.avg_score_after.toFixed(1) || 0}
                suffix="分"
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="累计提升"
                value={report.summary?.total_improvement || 0}
                suffix="分"
                valueStyle={{ color: '#1890ff' }}
                prefix={<FireOutlined />}
              />
            </Col>
          </Row>
        </Card>

        {/* Effect Distribution */}
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title={<><CheckCircleOutlined style={{ color: '#52c41a' }} /> 效果分布</>}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>优秀</Text>
                    <Text type="secondary">{report.effect_distribution?.excellent.toFixed(1)}%</Text>
                  </Space>
                  <Progress
                    percent={report.effect_distribution?.excellent || 0}
                    strokeColor="#52c41a"
                    showInfo={false}
                  />
                </div>
                <div>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>良好</Text>
                    <Text type="secondary">{report.effect_distribution?.good.toFixed(1)}%</Text>
                  </Space>
                  <Progress
                    percent={report.effect_distribution?.good || 0}
                    strokeColor="#1890ff"
                    showInfo={false}
                  />
                </div>
                <div>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>中等</Text>
                    <Text type="secondary">{report.effect_distribution?.moderate.toFixed(1)}%</Text>
                  </Space>
                  <Progress
                    percent={report.effect_distribution?.moderate || 0}
                    strokeColor="#faad14"
                    showInfo={false}
                  />
                </div>
                <div>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>较差</Text>
                    <Text type="secondary">{report.effect_distribution?.poor.toFixed(1)}%</Text>
                  </Space>
                  <Progress
                    percent={report.effect_distribution?.poor || 0}
                    strokeColor="#ff4d4f"
                    showInfo={false}
                  />
                </div>
              </Space>
            </Card>
          </Col>
          <Col span={12}>
            <Card title={<><WarningOutlined style={{ color: '#faad14' }} /> 层级辅导分布</>}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {Object.entries(report.level_distribution || {}).map(([level, count]) => (
                  <div key={level}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text>{levelNameMap[level] || level}</Text>
                      <Text type="secondary">{count} 次</Text>
                    </Space>
                    <Progress
                      percent={(count / (report.summary?.completed_coaching_sessions || 1)) * 100}
                      strokeColor="#722ed1"
                      showInfo={false}
                    />
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Learning Curve */}
        {curveData && curveData.has_data && (
          <Card
            title={<><LineChartOutlined /> 学习曲线</>}
            extra={
              <Segmented
                options={[
                  { label: '7天', value: 7 },
                  { label: '30天', value: 30 },
                  { label: '90天', value: 90 },
                ]}
                value={curveDays}
                onChange={(value) => setCurveDays(value as number)}
              />
            }
          >
            <div style={{ marginBottom: 16 }}>
              <Alert
                message={curveData.trend_analysis}
                type="info"
                showIcon
              />
            </div>
            <Line {...chartConfig} />
          </Card>
        )}

        {/* Recent Trends */}
        {report.recent_trends && report.recent_trends.length > 0 && (
          <Card title="最近辅导记录">
            <List
              dataSource={report.recent_trends}
              renderItem={(trend) => (
                <List.Item>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Space>
                      <Text type="secondary">{trend.date}</Text>
                      <Tag color="blue">{levelNameMap[trend.level]}</Tag>
                      <Tag color={getEffectivenessColor(trend.effectiveness)}>
                        {effectivenessTextMap[trend.effectiveness]}
                      </Tag>
                    </Space>
                    <Space>
                      <Text type="secondary">
                        {trend.score_before}分 → {trend.score_after}分
                      </Text>
                      <Text type={trend.improvement > 0 ? 'success' : 'danger'}>
                        {trend.improvement > 0 ? '+' : ''}{trend.improvement}分
                      </Text>
                    </Space>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Insights */}
        {report.insights && report.insights.length > 0 && (
          <Card title={<><BulbOutlined /> 洞察与建议</>}>
            <List
              dataSource={report.insights}
              renderItem={(insight) => (
                <List.Item>
                  <Text>{insight}</Text>
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Action Buttons */}
        <Card>
          <Space style={{ width: '100%', justifyContent: 'center' }}>
            <Button type="primary" size="large" onClick={() => navigate('/training')}>
              继续训练
            </Button>
            <Button size="large" onClick={() => window.location.reload()}>
              刷新报告
            </Button>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default CoachingEffectAnalysis;

# [PYAI-MP-08] 舵机与映射

> **模块**：MicroPython硬件开发
> **认知负荷**：中-高
> **核心技能**：SG90舵机控制(0-180度)、数值映射算法
> **UID**：PYAI-MP-08-001

---

## 课程基本信息

| 项目 | 内容 |
|------|------|
| **课程编号** | MP1-L8 |
| **课程名称** | 舵机与映射 |
| **认知负荷** | 中-高 |
| **核心技能** | SG90舵机控制(0-180度)、数值映射算法 |
| **项目内容** | 旋钮控制舵机 |

---

## 详细教学流程

**教师话术**
> "今天学习控制**舵机**——可以精确转动到指定角度的电机！"
>
> "**SG90舵机**：
> - 转动范围：0-180度
> - 用PWM信号控制角度
>
> **数值映射**：把一个范围的数值转换到另一个范围
> - 旋钮值：0-4095
> - 舵机角度：0-180
> - 映射公式：angle = knob_value * 180 / 4095"

---

## 核心代码模式

```python
from novaMP import SG90, NUB
import time

# 创建实例
servo = SG90(15)  # 舵机连接到Pin 15
knob = NUB(34)    # 旋钮连接到Pin 34

def map_value(value, in_min, in_max, out_min, out_max):
    """数值映射函数"""
    return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

while True:
    # 读取旋钮值
    knob_value = knob.read()

    # 映射到角度
    angle = map_value(knob_value, 0, 4095, 0, 180)

    # 控制舵机
    servo.move_to(angle)

    print(f"旋钮: {knob_value}, 角度: {angle}")
    time.sleep_ms(50)
```

---

## 禁忌提醒

- **强行扭动舵机**——会损坏内部齿轮（扫齿）
- **角度超出0-180范围**——舵机会卡死

---

`#执行层` `#测评项`
[UID: PYAI-23-MP1-L8-001]

---

[上一课](PYAI-MP-07_温湿度数据采集.md) | [模块概览](_模块概览.md) | [下一课](PYAI-MP-09_声光互动.md)

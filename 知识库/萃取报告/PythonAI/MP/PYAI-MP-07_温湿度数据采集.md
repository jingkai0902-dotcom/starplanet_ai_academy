# [PYAI-MP-07] 温湿度数据采集

> **模块**：MicroPython硬件开发
> **认知负荷**：中-高
> **核心技能**：DHT11传感器、RTC时间戳、文件操作、CSV保存
> **UID**：PYAI-MP-07-001

---

## 课程基本信息

| 项目 | 内容 |
|------|------|
| **课程编号** | MP1-L7 |
| **课程名称** | 温湿度数据采集 |
| **认知负荷** | 中-高 |
| **核心技能** | DHT11传感器、RTC时间戳、文件操作、CSV保存 |
| **项目内容** | 温湿度记录仪 |

---

## 详细教学流程

**教师话术**
> "今天我们用**DHT11传感器**采集温湿度数据，并保存到文件里！"
>
> "**DHT11注意事项**：
> - 两次读取之间必须间隔**至少1秒**
> - 否则会数据冲突或报错"

---

## 核心代码模式

```python
from novaMP import DHT11
from machine import RTC
import time

# 创建传感器实例
dht = DHT11(4)  # 连接到Pin 4
rtc = RTC()

# 读取数据
dht.measure()  # 触发测量
temp = dht.temperature  # 获取温度
humi = dht.humidity     # 获取湿度

print(f"温度: {temp}C, 湿度: {humi}%")

# 保存到文件
with open('data.csv', 'a') as f:
    timestamp = rtc.datetime()
    f.write(f"{timestamp},{temp},{humi}\n")

# 注意：下次读取前要等待1秒
time.sleep(1)
```

---

## 禁忌提醒

- **DHT11读取间隔<1秒**——会报错或数据不准
- **忘记调用measure()**——temperature/humidity不会更新

---

`#执行层` `#测评项`
[UID: PYAI-23-MP1-L7-001]

---

[上一课](PYAI-MP-06_硬件驱动封装.md) | [模块概览](_模块概览.md) | [下一课](PYAI-MP-08_舵机与映射.md)

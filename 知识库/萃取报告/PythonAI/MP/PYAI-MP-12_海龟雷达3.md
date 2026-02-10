# [PYAI-MP-12] 海龟雷达(3)

> **模块**：MicroPython硬件开发
> **认知负荷**：高
> **核心技能**：综合调试、Python海龟画图、数据可视化
> **UID**：PYAI-MP-12-001

---

## 课程基本信息

| 项目 | 内容 |
|------|------|
| **课程编号** | MP1-L12 |
| **课程名称** | 海龟雷达(3) |
| **认知负荷** | 高 |
| **核心技能** | 综合调试、Python海龟画图、数据可视化 |
| **项目内容** | 雷达扫描系统 |

---

## 详细教学流程

**教师话术**
> "最后一步，把所有功能整合起来！
> - 舵机扫描（0-180度）
> - 超声波测距
> - 串口发送数据
> - 电脑用Python海龟画图显示雷达图"

---

## 核心代码模式（ESP32端）

```python
from novaMP import SG90, HCSR04
from machine import UART
import time

servo = SG90(15)
sonar = HCSR04(trig=5, echo=18)
uart = UART(2, baudrate=9600, tx=17, rx=16)

# 雷达扫描
for angle in range(0, 181, 5):
    servo.move_to(angle)
    time.sleep_ms(100)

    distance = sonar.distance_cm()

    # 发送数据：角度,距离
    uart.write(f"{angle},{distance}\n")
```

---

## 电脑端接收代码（Python）

```python
import serial
import turtle

# 打开串口
ser = serial.Serial('COM3', 9600)

# 设置海龟画图
screen = turtle.Screen()
t = turtle.Turtle()
t.speed(0)

while True:
    if ser.in_waiting:
        line = ser.readline().decode().strip()
        angle, distance = map(int, line.split(','))

        # 绘制雷达扫描线
        t.setheading(angle)
        t.forward(distance)
        t.backward(distance)
```

---

## 评估标准

- 舵机能转动（0-180度扫描）
- 超声波能测距
- 电脑屏幕能画出雷达扫描图
- 重点：**功能实现优先，底层原理可略讲**

---

## 项目整合流程

```
1. 舵机转动到指定角度
       |
       v
2. 超声波测量距离
       |
       v
3. 串口发送数据（角度,距离）
       |
       v
4. 电脑接收数据
       |
       v
5. 海龟画图绘制雷达图
```

---

`#执行层` `#测评项`
[UID: PYAI-23-MP1-L12-001]

---

[上一课](PYAI-MP-11_海龟雷达2.md) | [模块概览](_模块概览.md) | [返回索引](../_索引.md)

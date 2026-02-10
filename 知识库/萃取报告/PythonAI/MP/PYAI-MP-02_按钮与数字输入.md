# [PYAI-MP-02] 按钮与数字输入

> **模块**：MicroPython硬件开发
> **认知负荷**：中
> **核心技能**：输入模式、Pin.IN、按键抖动、软件消抖
> **UID**：PYAI-MP-02-001

---

## 课程基本信息

| 项目 | 内容 |
|------|------|
| **课程编号** | MP1-L2 |
| **课程名称** | 按钮与数字输入 |
| **认知负荷** | 中 |
| **核心技能** | 输入模式、Pin.IN、按键抖动、软件消抖 |
| **项目内容** | 按钮控制LED |

---

## 详细教学流程

**步骤1：知识讲解（15分钟）** `#中负荷-操练` `#IFC-即时`

**教师话术**
> "上节课我们学会了用代码控制LED闪烁。但那是自动的，如果我想用按钮来控制呢？今天学习**GPIO输入**——让开发板'感知'按钮状态！"
>
> "**GPIO输入模式**：之前LED是输出(OUT)，按钮是输入(IN)
> ```python
> # LED是输出
> led = Pin(2, Pin.OUT)
>
> # 按钮是输入
> button = Pin(4, Pin.IN)
> ```
>
> **读取按钮状态**：用`value()`方法
> ```python
> state = button.value()
> # 返回 0 表示按下（低电平）
> # 返回 1 表示松开（高电平）
> ```
>
> **为什么按下是0？** 按钮接地(GND)，按下时引脚接地，电压为0"

---

## 核心代码模式

```python
from machine import Pin
import time

# 初始化引脚
led = Pin(2, Pin.OUT)
button = Pin(4, Pin.IN)

while True:
    if button.value() == 0:  # 按钮按下
        led.value(1)         # 开灯
    else:
        led.value(0)         # 关灯
    time.sleep_ms(20)        # 消抖延时
```

---

## 消抖处理（重点）

```python
# 切换开关实现
light_on = False  # 记录灯的状态
last_state = 1    # 记录上次按钮状态

while True:
    current_state = button.value()

    # 检测按下瞬间（从1变成0）
    if current_state == 0 and last_state == 1:
        light_on = not light_on  # 切换状态
        led.value(1 if light_on else 0)
        time.sleep_ms(200)  # 防止连续触发

    last_state = current_state
    time.sleep_ms(20)
```

---

## 变体示例

| 学生情况 | 调整方案 | 说明 |
|----------|----------|------|
| 不理解0和1 | 用开关类比 | "按下接通=0，松开断开=1" |
| 按钮不灵敏 | 检查接线 | 确认按钮一端接引脚，一端接GND |
| 切换不灵 | 检查边沿检测 | 确认是检测"按下瞬间"而非"按住" |

---

## 禁忌提醒

- **按钮两端都接VCC**——无法检测按下
- **忘记消抖**——按一次可能触发多次

---

`#执行层` `#测评项`
[UID: PYAI-23-MP1-L2-001]

---

[上一课](PYAI-MP-01_初识MicroPython.md) | [模块概览](_模块概览.md) | [下一课](PYAI-MP-03_模拟信号与PWM.md)

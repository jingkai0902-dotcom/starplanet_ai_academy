# AI知识总表

> **用途**：跨课程AI知识汇总，快速查找AI技术在各课程的应用
> **更新日期**：2026-02-10
> **数据来源**：萃取报告/PythonAI/
> **整合原则**：基于现有萃取报告，不压缩删减

---

## 快速导航

| 技术类别 | 包含内容 | 详情链接 |
|----------|---------|---------|
| 计算机视觉 | OpenCV、图像处理 | [计算机视觉.md](计算机视觉.md) |
| 人脸识别 | FaceMesh、特征匹配 | [人脸识别.md](人脸识别.md) |
| 手势识别 | MediaPipe Hands | [手势识别.md](手势识别.md) |

---

## AI技术总览

### 按课程分布

| 课程编号 | AI技术 | 具体应用 |
|----------|--------|---------|
| PYAI 1-4-6 | OpenCV基础 | 摄像头采集、人脸捕捉 |
| PYAI 1-4-7 | 特征匹配 | 人脸比对算法 |
| PYAI 1-4-8 | AI+硬件 | 刷脸开门系统 |
| PYAI 2-3-1 | MediaPipe FaceMesh | 眼睛关键点检测 |
| PYAI 2-3-2 | 眨眼检测 | 阈值判定、状态机 |
| PYAI 2-3-3 | 眼控开关 | AI+GPIO控制 |
| PYAI 2-3-5 | 表情识别 | 微笑/张嘴检测 |
| PYAI 2-3-6 | 表情强度 | 表情仪表盘 |
| PYAI 2-3-7 | MediaPipe Hands | 手部21关键点 |
| PYAI 2-3-8 | 手势控制 | 手势映射游戏 |
| PYAI 2-3-9 | 指尖追踪 | 空中绘画板 |
| PYAI 2-3-10/11 | 随机算法 | 猜拳机器人 |

---

## 一、计算机视觉基础

### 1.1 OpenCV库

#### 跨课程出现

| 课程编号 | 课程名称 | 具体内容 |
|----------|---------|---------|
| PYAI 1-4-6 | 智能门禁(1) | 摄像头采集 |
| PYAI 1-4-7 | 智能门禁(2) | 图像处理 |

#### 核心代码
```python
import cv2

# 打开摄像头
cap = cv2.VideoCapture(0)

while True:
    # 读取一帧
    ret, frame = cap.read()
    if not ret:
        break

    # 显示画面
    cv2.imshow('Camera', frame)

    # 按q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源（重要！）
cap.release()
cv2.destroyAllWindows()
```

### 1.2 图像处理

#### 灰度转换
```python
# 彩色图转灰度图
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
```

#### 图像绘制
```python
# 画线
cv2.line(frame, (0, 0), (100, 100), (255, 0, 0), 2)

# 画圆
cv2.circle(frame, (50, 50), 20, (0, 255, 0), -1)

# 画矩形
cv2.rectangle(frame, (10, 10), (100, 100), (0, 0, 255), 2)

# 写文字
cv2.putText(frame, 'Hello', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
```

---

## 二、人脸识别

### 2.1 人脸捕捉与比对

#### 跨课程出现

| 课程编号 | 课程名称 | 具体内容 |
|----------|---------|---------|
| PYAI 1-4-6 | 人脸捕捉 | 采集人脸图像 |
| PYAI 1-4-7 | 人脸比对 | 模板匹配算法 |
| PYAI 1-4-8 | 刷脸开门 | AI+舵机控制 |

#### 模板匹配
```python
import cv2

# 读取模板（已注册的人脸）
template = cv2.imread('registered_face.jpg', 0)

# 读取当前帧并转灰度
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# 模板匹配
result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)

# 获取最大匹配值
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

# 判断是否匹配
if max_val > 0.8:  # 相似度阈值
    print("人脸匹配成功！")
    # 控制舵机开门
    servo.write_angle(90)
```

### 2.2 MediaPipe FaceMesh

#### 跨课程出现

| 课程编号 | 课程名称 | 具体内容 |
|----------|---------|---------|
| PYAI 2-3-1 | FaceMesh基础 | 468个面部关键点 |
| PYAI 2-3-2 | 眨眼检测 | 眼睛关键点距离 |

#### 核心代码
```python
import cv2
import mediapipe as mp

# 初始化FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    min_detection_confidence=0.5
)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 转换颜色空间
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 检测人脸
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # 获取关键点
            for idx, landmark in enumerate(face_landmarks.landmark):
                h, w, c = frame.shape
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                # 绘制关键点
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

    cv2.imshow('FaceMesh', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### 2.3 眨眼检测

#### 关键点索引
```
左眼上眼皮: 159
左眼下眼皮: 145
右眼上眼皮: 386
右眼下眼皮: 374
```

#### 眨眼检测代码
```python
def get_eye_distance(landmarks, upper_idx, lower_idx):
    """计算眼睛开合距离"""
    upper = landmarks[upper_idx]
    lower = landmarks[lower_idx]
    return abs(upper.y - lower.y)

# 检测眨眼
left_eye_dist = get_eye_distance(landmarks, 159, 145)
right_eye_dist = get_eye_distance(landmarks, 386, 374)
avg_eye_dist = (left_eye_dist + right_eye_dist) / 2

# 阈值判断
BLINK_THRESHOLD = 0.02
if avg_eye_dist < BLINK_THRESHOLD:
    print("检测到眨眼！")
```

---

## 三、表情识别

### 跨课程出现

| 课程编号 | 课程名称 | 具体内容 |
|----------|---------|---------|
| PYAI 2-3-5 | 表情音乐播放器 | 微笑/张嘴检测 |
| PYAI 2-3-6 | 表情仪表盘 | 表情强度计算 |

### 3.1 微笑检测

#### 关键点索引
```
嘴角左: 61
嘴角右: 291
嘴巴中心: 13
```

#### 微笑检测代码
```python
def detect_smile(landmarks):
    """检测微笑"""
    left_corner = landmarks[61]
    right_corner = landmarks[291]
    mouth_center = landmarks[13]

    # 嘴角上扬判断
    left_lift = mouth_center.y - left_corner.y
    right_lift = mouth_center.y - right_corner.y

    if left_lift > 0.01 and right_lift > 0.01:
        return True, (left_lift + right_lift) / 2
    return False, 0
```

### 3.2 张嘴检测

#### 关键点索引
```
上嘴唇: 13
下嘴唇: 14
```

#### 张嘴检测代码
```python
def detect_mouth_open(landmarks):
    """检测张嘴"""
    upper_lip = landmarks[13]
    lower_lip = landmarks[14]

    mouth_open = abs(upper_lip.y - lower_lip.y)

    MOUTH_THRESHOLD = 0.05
    return mouth_open > MOUTH_THRESHOLD
```

---

## 四、手势识别

### 跨课程出现

| 课程编号 | 课程名称 | 具体内容 |
|----------|---------|---------|
| PYAI 2-3-7 | MediaPipe Hands | 21个手部关键点 |
| PYAI 2-3-8 | 手势控制 | 手势映射 |
| PYAI 2-3-9 | 指尖追踪 | 空中绘画 |

### 4.1 手部关键点

```
手部21个关键点索引：
0  - 手腕
1-4   - 拇指（1=根部, 4=指尖）
5-8   - 食指（5=根部, 8=指尖）
9-12  - 中指（9=根部, 12=指尖）
13-16 - 无名指（13=根部, 16=指尖）
17-20 - 小拇指（17=根部, 20=指尖）
```

### 4.2 手势识别代码

```python
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7
)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # 获取关键点
            landmarks = hand_landmarks.landmark

            # 判断手指是否伸直
            fingers_up = []

            # 拇指（比较x坐标）
            if landmarks[4].x < landmarks[3].x:
                fingers_up.append(1)
            else:
                fingers_up.append(0)

            # 其他四指（比较y坐标，指尖低于第二关节）
            for tip_idx in [8, 12, 16, 20]:
                if landmarks[tip_idx].y < landmarks[tip_idx - 2].y:
                    fingers_up.append(1)
                else:
                    fingers_up.append(0)

            print(f"手指状态: {fingers_up}")

    cv2.imshow('Hands', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### 4.3 手势映射

```python
# 手势到指令的映射
GESTURE_MAP = {
    (0, 1, 0, 0, 0): 'UP',      # 只伸食指 = 上
    (0, 1, 1, 0, 0): 'DOWN',    # 食指+中指 = 下
    (1, 1, 1, 1, 1): 'STOP',    # 全部伸开 = 停止
    (0, 0, 0, 0, 0): 'FIST',    # 握拳
}

def get_gesture(fingers_up):
    return GESTURE_MAP.get(tuple(fingers_up), 'UNKNOWN')
```

### 4.4 指尖追踪绘画

```python
# 获取食指指尖坐标
index_tip = landmarks[8]
h, w, c = frame.shape
x = int(index_tip.x * w)
y = int(index_tip.y * h)

# 绘制轨迹
if prev_x is not None:
    cv2.line(canvas, (prev_x, prev_y), (x, y), draw_color, 5)

prev_x, prev_y = x, y
```

---

## 五、AIoT系统集成

### 架构模式

```
┌─────────────────────────────────────┐
│           应用层（执行）              │
│   LED、舵机、蜂鸣器、屏幕显示         │
└─────────────────────────────────────┘
                   ↑
┌─────────────────────────────────────┐
│           处理层（AI决策）            │
│   MediaPipe、OpenCV、状态机          │
└─────────────────────────────────────┘
                   ↑
┌─────────────────────────────────────┐
│           感知层（输入）              │
│   摄像头、传感器                      │
└─────────────────────────────────────┘
```

### 典型项目

| 项目 | 感知 | AI处理 | 执行 |
|------|------|--------|------|
| 眼控开关 | 摄像头 | 眨眼检测 | LED |
| 刷脸门禁 | 摄像头 | 人脸匹配 | 舵机 |
| 手势控制 | 摄像头 | 手势识别 | 游戏/硬件 |
| 表情音乐 | 摄像头 | 表情识别 | 音频播放 |

---

## 六、常见错误与禁忌

| 错误 | 后果 | 正确做法 |
|------|------|---------|
| ❌ 忘记释放摄像头 | 下次无法使用 | 程序结束前调用`cap.release()` |
| ❌ BGR/RGB颜色空间混淆 | 颜色显示错误 | OpenCV用BGR，MediaPipe用RGB |
| ❌ 阈值设置不当 | 识别不准确 | 根据实际环境调整阈值 |
| ❌ 未处理检测失败 | 程序崩溃 | 检查`results`是否为None |

---

**维护者**：���识库管理员
**数据来源**：萃取报告/PythonAI/
**整合原则**：基于现有萃取报告，不压缩删减

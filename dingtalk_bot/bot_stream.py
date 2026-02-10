#!/usr/bin/env python3
"""
斯坦星球知识库钉钉机器人 - Stream模式
使用钉钉Stream SDK，无需公网IP
"""

import json
import logging
import re
import asyncio
from pathlib import Path

import requests
import dingtalk_stream
from dingtalk_stream import AckMessage
from dingtalk_stream.chatbot import ChatbotHandler, ChatbotMessage

# 配置日志 - 输出到文件
log_file = Path(__file__).parent / "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== 配置区域 ==============
CONFIG = {
    "app_key": "",
    "app_secret": "",
    "kb_path": "",
    "llm_provider": "zhipu",
    "llm_api_key": "",
    "llm_base_url": "https://open.bigmodel.cn/api/paas/v4",
    "llm_model": "glm-4.7",
    "claude_api_key": "",
    "claude_base_url": "",
}

# ============== 知识库 ==============
KB_DOCUMENTS = []

# ============== 消息去重 ==============
# 存储已处理的消息ID（最多保留1000条）
PROCESSED_MESSAGES = set()
MAX_PROCESSED_MESSAGES = 1000

# ============== 用户会话记忆 ==============
# 存储每个用户的对话上下文 {sender_id: {"course_type": "STEM", "course_id": "1-1-02", "topic": "自制表情包", "last_query": "...", "timestamp": ...}}
import time
USER_SESSIONS = {}
SESSION_TIMEOUT = 600  # 会话超时时间（秒），10分钟


def get_message_id(incoming_message) -> str:
    """从消息中提取唯一ID"""
    if isinstance(incoming_message, dict):
        # 尝试多种可能的ID字段
        msg_id = incoming_message.get("msgId") or incoming_message.get("conversationId") or incoming_message.get("createAt")
        if msg_id:
            return str(msg_id)
        # 用内容+发送者+时间生成伪ID
        content = incoming_message.get("text", {})
        if isinstance(content, dict):
            content = content.get("content", "")
        sender = incoming_message.get("senderId", "")
        return f"{sender}_{hash(content)}_{incoming_message.get('createAt', '')}"
    else:
        # ChatbotMessage对象
        msg_id = getattr(incoming_message, 'msg_id', None) or getattr(incoming_message, 'conversation_id', None)
        if msg_id:
            return str(msg_id)
        content = ""
        if hasattr(incoming_message, 'text') and incoming_message.text:
            if hasattr(incoming_message.text, 'content'):
                content = incoming_message.text.content
        sender = getattr(incoming_message, 'sender_id', '')
        return f"{sender}_{hash(content)}"


def is_duplicate_message(msg_id: str) -> bool:
    """检查消息是否已处理过"""
    if msg_id in PROCESSED_MESSAGES:
        return True
    
    # 添加到已处理集合
    PROCESSED_MESSAGES.add(msg_id)
    
    # 如果超过最大数量，清理旧的
    if len(PROCESSED_MESSAGES) > MAX_PROCESSED_MESSAGES:
        # 简单清理：删除一半
        to_remove = list(PROCESSED_MESSAGES)[:MAX_PROCESSED_MESSAGES // 2]
        for item in to_remove:
            PROCESSED_MESSAGES.discard(item)
    
    return False


def get_user_session(sender_id: str) -> dict:
    """获取用户会话，过期则返回空"""
    session = USER_SESSIONS.get(sender_id)
    if session:
        if time.time() - session.get("timestamp", 0) < SESSION_TIMEOUT:
            return session
        else:
            # 会话过期，删除
            del USER_SESSIONS[sender_id]
    return {}


def update_user_session(sender_id: str, course_type: str = None, course_id: str = None, topic: str = None, last_query: str = None):
    """更新用户会话"""
    session = USER_SESSIONS.get(sender_id, {})
    session["timestamp"] = time.time()
    
    if course_type:
        session["course_type"] = course_type
    if course_id:
        session["course_id"] = course_id
    if topic:
        session["topic"] = topic
    if last_query:
        session["last_query"] = last_query
    
    USER_SESSIONS[sender_id] = session


def extract_topic_from_content(content: str, course_id: str = None) -> str:
    """从内容中提取课程主题"""
    # 常见课程名称映射
    topic_patterns = [
        (r"自制表情包", "自制表情包"),
        (r"独一无二的我", "独一无二的我"),
        (r"眼球的奥秘", "眼球的奥秘"),
        (r"舌尖的旅行", "舌尖的旅行"),
        (r"小鼻子大本事", "小鼻子大本事"),
        (r"奇妙大耳朵", "奇妙大耳朵"),
        (r"超级能手", "超级能手"),
        (r"摇摆的身体", "摇摆的身体"),
        (r"深呼吸", "深呼吸"),
        (r"我的小心脏", "我的小心脏"),
        (r"怕酸的牙齿", "怕酸的牙齿"),
        (r"人体迷宫", "人体迷宫"),
    ]
    
    for pattern, topic in topic_patterns:
        if re.search(pattern, content):
            return topic
    
    return None


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            CONFIG.update(loaded)

    if not CONFIG["kb_path"]:
        CONFIG["kb_path"] = str(Path(__file__).parent / "knowledge_base")


def build_content_from_sections(sections: list) -> str:
    """将sections合并为可检索的正文内容"""
    parts = []
    for sec in sections or []:
        if not isinstance(sec, dict):
            continue
        title = (sec.get("title") or "").strip()
        content = (sec.get("content") or "").strip()
        if not title and not content:
            continue
        if title:
            parts.append(f"## {title}\n{content}".strip())
        else:
            parts.append(content)
    return "\n\n".join([p for p in parts if p])


def load_knowledge_base():
    """加载知识库所有文档"""
    kb_dir = Path(CONFIG["kb_path"])
    documents = []

    if not kb_dir.exists():
        logger.error(f"知识库目录不存在: {kb_dir}")
        return []

    for json_file in kb_dir.glob("*.json"):
        if json_file.name == "_index.json":
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "entries" in data:
                for entry in data["entries"]:
                    documents.append({
                        "title": entry.get("title", ""),
                        "source": json_file.name,
                        "content": entry.get("content", {}).get("raw", ""),
                        "sections": []
                    })
            elif "title" in data:
                sections = data.get("sections", [])
                content = data.get("full_content") or build_content_from_sections(sections) or data.get("content", "")
                if content:
                    documents.append({
                        "title": data.get("title", ""),
                        "source": data.get("source", json_file.name),
                        "content": content,
                        "sections": sections
                    })
        except Exception as e:
            logger.warning(f"无法加载 {json_file.name}: {e}")

    logger.info(f"已加载 {len(documents)} 个文档")
    return documents


# ============== 知识库搜索 ==============

def extract_query_terms(query: str) -> list[str]:
    """提取查询关键词（支持中文、数字、课程编号）"""
    query_lower = query.lower()
    terms = set()

    # 英文/数字连续片段
    for token in re.findall(r"[a-z0-9]+", query_lower):
        terms.add(token)

    # 课程编号（如 1-1-2）
    for token in re.findall(r"\d+(?:-\d+)+", query_lower):
        terms.add(token)
        parts = token.split("-")
        if len(parts) >= 2:
            terms.add("-".join(parts[:2]))

    # 中文连续片段与二字切分
    for token in re.findall(r"[\u4e00-\u9fff]+", query_lower):
        terms.add(token)
        if len(token) >= 2:
            for i in range(len(token) - 1):
                terms.add(token[i:i + 2])

    if not terms:
        terms.add(query_lower.strip())

    return list(terms)


def extract_snippet(content: str, terms: list[str], before: int = 400, after: int = 1200) -> str | None:
    """从内容中截取包含关键词的片段"""
    if not content or not terms:
        return None
    content_lower = content.lower()
    best = None  # (count, pos)
    best_pos = None
    for term in terms:
        if not term:
            continue
        if len(term) < 2:
            continue
        pos = content_lower.find(term)
        if pos == -1:
            continue
        count = content_lower.count(term)
        candidate = (count, pos)
        if best is None or candidate < best:
            best = candidate
            best_pos = pos
    if best_pos is None:
        return None
    start = max(best_pos - before, 0)
    end = min(best_pos + after, len(content))
    return content[start:end]


def extract_course_id(query: str) -> str | None:
    """提取课程编号（如 1-1-2）"""
    match = re.search(r"\d+(?:-\d+)+", query)
    if match:
        return match.group(0)
    return None


def normalize_course_id(course_id: str) -> list[str]:
    """生成课程编号的所有可能变体（处理前导零）
    例如 '1-1-2' -> ['1-1-2', '1-1-02', '1-01-2', '1-01-02', '01-1-2', ...]
    """
    if not course_id:
        return []
    
    parts = course_id.split("-")
    variants = set()
    
    # 原始版本
    variants.add(course_id)
    
    # 生成带前导零和不带前导零的变体
    def generate_variants(parts_list, index=0, current=[]):
        if index == len(parts_list):
            variants.add("-".join(current))
            return
        
        part = parts_list[index]
        # 不带前导零
        current.append(part.lstrip("0") or "0")
        generate_variants(parts_list, index + 1, current)
        current.pop()
        
        # 带前导零（两位数格式）
        if len(part) == 1:
            current.append("0" + part)
            generate_variants(parts_list, index + 1, current)
            current.pop()
    
    generate_variants(parts)
    return list(variants)


def detect_course_type(query: str) -> str | None:
    """检测查询中的课程类型"""
    query_lower = query.lower()
    
    # STEM幼儿课程关键词
    if any(kw in query_lower for kw in ["小班", "中班", "大班", "幼儿", "stem", "3岁", "4岁", "5岁", "6岁", "认识我自己", "动物王国", "植物奥秘", "数理物理", "机械与工具", "建筑与结构", "智能机械", "物理科学", "复杂机械", "地球与空间", "能源科学", "智能硬件"]):
        return "STEM"
    
    # PythonAI课程关键词
    if any(kw in query_lower for kw in ["python", "pythonai", "人工智能", "ai课", "l1", "l2", "函数", "算法", "数据结构", "计算机视觉", "仿生"]):
        return "PythonAI"
    
    # CODE少儿编程关键词
    if any(kw in query_lower for kw in ["code1", "code2", "code3", "scratch", "少儿编程", "编程启蒙", "游戏开发"]):
        return "CODE"
    
    # C++信奥关键词
    if any(kw in query_lower for kw in ["信奥", "c++", "noi", "csp", "竞赛"]):
        return "CPP"
    
    return None


def filter_documents_by_type(documents: list, course_type: str) -> list:
    """根据课程类型过滤文档"""
    if not course_type:
        return documents
    
    filtered = []
    for doc in documents:
        title = doc.get("title", "").upper()
        source = doc.get("source", "").upper()
        
        if course_type == "STEM":
            # STEM文档：标题或来源包含STEM/小班/中班/大班
            if any(kw in title or kw in source for kw in ["STEM", "小班", "中班", "大班"]):
                filtered.append(doc)
        elif course_type == "PythonAI":
            if "PYTHON" in title or "PYTHON" in source:
                filtered.append(doc)
        elif course_type == "CODE":
            if "CODE" in title or "CODE" in source:
                filtered.append(doc)
        elif course_type == "CPP":
            if any(kw in title or kw in source for kw in ["C++", "信奥", "NOI", "CSP"]):
                filtered.append(doc)
    
    return filtered if filtered else documents  # 如果过滤后为空，返回全部


def find_course_matches(course_id: str, documents: list, course_type: str = None) -> list[dict]:
    """按课程编号精确匹配文档，生成包含片段的上下文"""
    matches = []
    
    # 生成课程编号的所有变体（处理前导零问题）
    course_id_variants = normalize_course_id(course_id)
    
    # 创建匹配所有变体的正则表达式
    pattern_str = "|".join(re.escape(v) for v in course_id_variants)
    pattern = re.compile(pattern_str)
    
    for doc in documents:
        found = False
        
        # 1. 先尝试在content中匹配
        content = doc.get("content", "")
        if content:
            hit = pattern.search(content)
            if hit:
                start = max(hit.start() - 600, 0)
                end = min(hit.end() + 1200, len(content))
                snippet = content[start:end]
                matches.append({
                    "title": doc.get("title", "未知"),
                    "source": doc.get("source", ""),
                    "content": snippet
                })
                found = True

        # 2. 在 sections 中匹配（无论content是否有内容）
        if not found:
            sections = doc.get("sections", [])
            for sec in sections:
                if not isinstance(sec, dict):
                    continue
                sec_content = sec.get("content", "")
                hit = pattern.search(sec_content)
                if hit:
                    # 提取匹配点附近的内容
                    start = max(hit.start() - 300, 0)
                    end = min(hit.end() + 1500, len(sec_content))
                    snippet = sec_content[start:end]
                    matches.append({
                        "title": f"{doc.get('title', '未知')} - {sec.get('title', '')}",
                        "source": doc.get("source", ""),
                        "content": snippet
                    })
                    break
        
        # 3. 也检查 full_content 字段
        if not found:
            full_content = doc.get("full_content", "")
            if full_content:
                hit = pattern.search(full_content)
                if hit:
                    start = max(hit.start() - 600, 0)
                    end = min(hit.end() + 1500, len(full_content))
                    snippet = full_content[start:end]
                    matches.append({
                        "title": doc.get("title", "未知"),
                        "source": doc.get("source", ""),
                        "content": snippet
                    })

    return matches


def search_documents(query: str, documents: list, max_results: int = 5) -> list:
    """搜索相关文档"""
    query_lower = query.lower()
    query_terms = extract_query_terms(query)
    results = []

    for doc in documents:
        score = 0
        title_raw = doc.get("title", "")
        content_raw = doc.get("content", "")
        sections = doc.get("sections", [])
        section_text = []
        if sections:
            for sec in sections:
                if isinstance(sec, dict):
                    section_text.append(sec.get("title", ""))
                    section_text.append(sec.get("content", ""))
        content_raw_combined = content_raw
        if section_text:
            content_raw_combined = content_raw + "\n" + "\n".join(section_text)

        title = title_raw.lower()
        content = content_raw_combined.lower()

        for term in query_terms:
            if term in title:
                score += 10
            if term in content:
                score += 3 + content.count(term)

        # 斯坦星球专用关键词加权
        keywords = {
            "stem": ["stem", "幼儿", "科创", "机械", "建筑", "物理"],
            "小班": ["小班", "3-4岁", "认识我自己", "动物", "植物"],
            "中班": ["中班", "4-5岁", "机械", "建筑", "智能"],
            "大班": ["大班", "5-6岁", "复杂机械", "能源", "空间", "智能硬件"],
            "code": ["code", "scratch", "编程", "少儿编程", "游戏开发"],
            "code1": ["code1", "机械结构", "智能硬件", "编程启蒙"],
            "code2": ["code2", "智能应用", "智能交互", "算法逻辑"],
            "code3": ["code3", "智能系统", "游戏开发", "高级工程"],
            "python": ["python", "pythonai", "人工智能", "ai"],
            "l1": ["l1", "函数", "算法", "数据结构"],
            "l2": ["l2", "数据科学", "计算机视觉", "cv", "仿生"],
            "信奥": ["信奥", "c++", "noi", "csp", "竞赛"],
            "销售": ["销售", "话术", "咨询", "异议", "促单"],
            "家长": ["家长", "沟通", "续费", "转介绍"],
        }

        for key, terms in keywords.items():
            if any(t in query_lower for t in terms):
                if any(t in title or t in content for t in terms):
                    score += 5

        if score > 0:
            doc["_score"] = score
            snippet = extract_snippet(content_raw_combined, query_terms)
            if snippet:
                doc["_snippet"] = snippet
            results.append(doc)

    results.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return results[:max_results]


def build_context(documents: list, max_chars: int = 8000) -> str:
    """构建上下文"""
    context_parts = []
    total_chars = 0

    for doc in documents:
        title = doc.get("title", "未知")
        content = doc.get("_snippet") or doc.get("content", "")

        if total_chars + len(content) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 500:
                content = content[:remaining] + "\n...(内容截断)"
            else:
                break

        context_parts.append(f"### {title}\n\n{content}")
        total_chars += len(content)

    return "\n\n---\n\n".join(context_parts)


# ============== LLM API ==============

def get_llm_config():
    """获取大模型配置（优先读取llm_*, 兼容claude_*）"""
    api_key = CONFIG.get("llm_api_key") or CONFIG.get("claude_api_key") or ""
    base_url = CONFIG.get("llm_base_url") or CONFIG.get("claude_base_url") or "https://open.bigmodel.cn/api/paas/v4"
    model = CONFIG.get("llm_model") or "glm-4.7"
    return api_key, base_url, model


def clean_markdown(text: str) -> str:
    """清理Markdown格式符号，转为纯文本"""
    if not text:
        return text
    
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', lambda m: m.group(0).replace('```', '').strip(), text)
    
    # 移除行内代码
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 移除加粗
    text = re.sub(r'\*\*([^*]+)\*\*', r'【\1】', text)
    text = re.sub(r'__([^_]+)__', r'【\1】', text)
    
    # 移除斜体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # 移除标题符号
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # 移除分隔线
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^_{3,}$', '', text, flags=re.MULTILINE)
    
    # 将Markdown列表符号替换为更友好的符号
    text = re.sub(r'^[-*+]\s+', '· ', text, flags=re.MULTILINE)
    
    # 移除链接格式，保留文字
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def ask_llm(question: str, context: str) -> str:
    """调用大模型生成回答（智谱OpenAI兼容接口）"""
    api_key, base_url, model = get_llm_config()
    if not api_key:
        return "错误：未配置大模型API密钥"

    system_prompt = """你是斯坦星球的知识库助手，专门回答老师和销售顾问关于课程、教学、销售的问题。

斯坦星球简介：
- 专注于STEM科创和编程教育
- 课程体系：STEM幼儿科创（3-6岁）→ CODE少儿编程（6-12岁）→ PythonAI（10岁+）→ C++信奥
- 教学理念：项目制学习(PBL)、八大能力培养、做中学

重要规则：
1. 只能基于提供的知识库内容回答，不要编造任何信息
2. 如果知识库中没有相关内容，明确说"这个问题我在知识库中没有找到相关资料，建议咨询教学主管"
3. 回答要简洁实用，直接给出答案
4. 涉及具体课程、年龄、级别时，必须严格按照知识库内容
5. 用口语化的方式回答，像同事之间的对话

格式要求（非常重要！）：
- 输出纯文本，不要使用任何Markdown格式
- 不要用 **加粗** 或 *斜体*
- 不要用 ## 标题 或 ### 小标题
- 不要用 ``` 代码块
- 不要用 --- 分隔线
- 不要用 | 表格 |
- 用【】或「」来强调重点，用空行分段
- 用数字1. 2. 3.或符号•来列举，不要用-

课程体系要点（必须严格遵守）：
- STEM：小班(3-4岁)→中班(4-5岁)→大班(5-6岁)，每阶段4个主题
- CODE：CODE1(6-8岁)→CODE2(8-10岁)→CODE3(10-12岁)，机械+编程结合
- PythonAI：L1(10-12岁)→L2(12岁+)，人工智能方向
- C++信奥：面向竞赛的专业课程"""

    user_message = f"""请基于以下知识库内容回答问题。

【知识库内容】
{context}

【用户问题】
{question}

请直接回答，不要说"根据知识库"之类的开场白。"""

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
        "thinking": {"type": "disabled"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            logger.error(f"LLM错误: {resp.status_code} {resp.text[:300]}")
            return "抱歉，AI服务暂时不可用，请稍后再试。"
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            logger.error(f"LLM返回空内容: {data}")
            return "抱歉，AI服务暂时不可用，请稍后再试。"
        return clean_markdown(content)
    except Exception as e:
        logger.exception(f"LLM调用异常: {type(e).__name__}: {e}")
        return f"抱歉，AI服务暂时不可用，请稍后再试。(错误: {type(e).__name__})"


def is_follow_up_query(question: str) -> bool:
    """检测是否是跟进性问题（需要上下文的模糊查询）"""
    follow_up_patterns = [
        r"^展开", r"^详细", r"^继续", r"^再说说", r"^还有吗", r"^更多",
        r"^细说", r"^具体", r"怎么[办做]", r"^接着说", r"^然后呢",
        r"^还能.*吗", r"^可以.*吗", r"^能不能", r"^帮我.*展开",
        r"^说详细", r"^讲讲", r"^聊聊",
    ]
    question_lower = question.strip()
    for pattern in follow_up_patterns:
        if re.search(pattern, question_lower):
            return True
    # 太短的问题可能是跟进
    if len(question_lower) < 10 and not extract_course_id(question_lower):
        return True
    return False


def process_question(question: str, sender_id: str = "") -> str:
    """处理用户问题"""
    
    # 0. 获取用户会话上下文
    session = get_user_session(sender_id) if sender_id else {}
    
    # 1. 检测课程类型（小班/中班/大班/CODE/Python等）
    course_type = detect_course_type(question)
    course_id = extract_course_id(question)
    
    # 2. 检测是否是跟进性问题
    if is_follow_up_query(question) and not course_type and not course_id:
        # 从会话中恢复上下文
        if session:
            course_type = session.get("course_type")
            course_id = session.get("course_id")
            topic = session.get("topic")
            last_query = session.get("last_query", "")
            
            if course_type or course_id:
                logger.info(f"跟进查询，使用会话上下文: type={course_type}, id={course_id}, topic={topic}")
                # 将上下文信息补充到问题中
                if topic:
                    question = f"关于{topic}，{question}"
                elif course_id:
                    question = f"关于课程{course_id}，{question}"
    
    # 3. 根据课程类型预先过滤文档范围
    filtered_docs = filter_documents_by_type(KB_DOCUMENTS, course_type)
    
    # 4. 提取课程编号并在过滤后的范围内搜索
    if course_id:
        course_docs = find_course_matches(course_id, filtered_docs, course_type)
        if course_docs:
            context = build_context(course_docs, max_chars=8000)
            
            # 尝试从上下文中提取主题
            topic = extract_topic_from_content(context, course_id)
            
            # 更新会话
            if sender_id:
                update_user_session(sender_id, course_type, course_id, topic, question)
            
            return ask_llm(question, context)

    # 5. 如果没有课程编号匹配，用关键词搜索
    relevant_docs = search_documents(question, filtered_docs, max_results=5)

    if not relevant_docs:
        return "抱歉，没有找到与您问题相关的内容。请尝试换个关键词，或咨询教学主管。"

    context = build_context(relevant_docs)
    
    # 更新会话
    if sender_id:
        topic = extract_topic_from_content(context)
        update_user_session(sender_id, course_type, course_id, topic, question)
    
    return ask_llm(question, context)


# ============== 快捷命令 ==============

def handle_shortcut(cmd: str) -> str:
    """处理快捷命令"""
    cmd = cmd.lower()
    
    if cmd == "stem":
        return """📘 STEM幼儿科创课程（3-6岁）

【小班 3-4岁】
阶段1：认识我自己 - 身体部位、感官探索
阶段2：动物王国 - 动物特征、仿生设计
阶段3：植物奥秘 - 植物生长、观察记录
阶段4：数理物理 - 基础物理、数学启蒙

【中班 4-5岁】
阶段1：机械与工具 - 杠杆、滑轮、齿轮
阶段2：建筑与结构 - 桥梁、塔楼、稳定性
阶段3：智能机械 - 电动马达、传动系统
阶段4：物理科学 - 声光电热探索

【大班 5-6岁】
阶段1：复杂机械 - 综合机械系统
阶段2：地球与空间 - 天文、地理
阶段3：能源科学 - 新能源、电路
阶段4：智能硬件 - 编程初体验

💡 想了解更多？可以问我具体课时内容"""

    elif cmd == "code":
        return """💻 CODE少儿编程课程（6-12岁）

【CODE1 6-8岁】乐高+Scratch启蒙
• 模块1：机械结构基础
• 模块2：智能硬件与仿生
• 模块3：Scratch编程启蒙
• 模块4：编程逻辑进阶

【CODE2 8-10岁】进阶编程
• 模块1：智能生活应用
• 模块2：智能交互系统
• 模块3：算法与数学逻辑

【CODE3 10-12岁】高级工程
• 模块1：智能系统设计
• 模块2：游戏开发PBL
• 模块3：高级机械工程

特色：机械搭建+图形化编程+逻辑思维

💡 想了解升班规则？问我 CODE怎么升班"""

    elif cmd == "python":
        return """🐍 PythonAI课程（10岁+）

【L1阶段 10-12岁】Python基础+AI启蒙
• 模块0：基础语法与逻辑启蒙
• 模块1：函数封装与交互机制
• 模块2：算法逻辑与数值运算
• 模块3：数据结构与复杂逻辑
• 模块4：智能硬件与AI应用

【L2阶段 12岁+】AI进阶
• 模块1：算法与数据科学
• 模块2：AI对话与智能体
• 模块3：交互式AI与仿生控制
• 模块4：计算机视觉(CV)

特色：实战项目驱动、AI应用开发

💡 想了解入学评估？问我 Python怎么测评"""

    elif cmd in ["价格", "促单"]:
        return """💰 常见价格异议处理

【太贵了】
✅ 认同 → 拆分价值 → 对比投入
"理解您的顾虑。咱们拆开算一下，XX课时平均每次课XX元，一周X次，学下来孩子能获得..."

【再考虑】
✅ 认同 → 探询真实原因 → 解决顾虑
"完全理解，那您主要是想考虑哪方面呢？是时间安排还是...？"

【别家便宜】
✅ 不否定 → 差异化 → 价值锚定
"是的，市面上价格区间很大。咱们的特点是...您可以对比一下课程内容和师资..."

💡 想要更多话术？问我 异议处理"""

    return None


# ============== 处理单条消息 ==============

def handle_message(content: str, sender_nick: str, sender_id: str = "") -> str:
    """处理用户消息并返回回复"""
    content = content.strip()
    
    if not content:
        return ""

    # 帮助命令
    if content in ["帮助", "help", "?"]:
        return """🤖 斯坦星球知识库助手

直接输入问题即可，例如：
• STEM小班学什么内容？
• CODE1和CODE2有什么区别？
• 家长问Python有什么用怎么回答？
• 孩子多大可以学编程？
• 家长说价格贵怎么处理？

📚 支持的知识领域：
• 课程体系（STEM/CODE/PythonAI/C++信奥）
• 销售话术与异议处理
• 教学方法与课堂管理
• 家长沟通技巧

⚡ 快捷命令：
• /stem - STEM课程介绍
• /code - CODE编程课程
• /python - PythonAI课程
• /价格 - 价格异议处理

💡 提示：您也可以私聊我，获得更专注的服务"""

    # 快捷命令
    if content.startswith("/"):
        cmd = content[1:].strip()
        shortcut_reply = handle_shortcut(cmd)
        if shortcut_reply:
            return shortcut_reply

    # 普通问答（传入sender_id用于会话管理）
    return process_question(content, sender_id)


# ============== 钉钉消息处理器 ==============

class StarplanetKnowledgeHandler(ChatbotHandler):
    """斯坦星球知识库机器人消息处理器"""

    async def process(self, callback):
        """处理收到的消息"""
        try:
            incoming_message = callback.data
            logger.info(f"收到回调, 类型: {type(incoming_message)}")
            
            # ====== 消息去重检查 ======
            msg_id = get_message_id(incoming_message)
            if is_duplicate_message(msg_id):
                logger.info(f"重复消息，跳过: {msg_id}")
                return AckMessage.STATUS_OK, "OK"
            
            # 尝试获取消息内容
            content = ""
            sender_nick = "用户"
            sender_id = ""
            
            if isinstance(incoming_message, dict):
                # 字典格式
                text_obj = incoming_message.get("text", {})
                if isinstance(text_obj, dict):
                    content = text_obj.get("content", "")
                elif isinstance(text_obj, str):
                    content = text_obj
                sender_nick = incoming_message.get("senderNick", "用户")
                sender_id = incoming_message.get("senderId", "") or incoming_message.get("senderStaffId", "")
                logger.info(f"字典格式 - 用户: {sender_nick}, ID: {sender_id}, 内容: {content[:50] if content else '(空)'}")
            else:
                # ChatbotMessage对象
                if hasattr(incoming_message, 'text') and incoming_message.text:
                    if hasattr(incoming_message.text, 'content'):
                        content = incoming_message.text.content
                    else:
                        content = str(incoming_message.text)
                sender_nick = getattr(incoming_message, 'sender_nick', '用户') or "用户"
                sender_id = getattr(incoming_message, 'sender_id', '') or getattr(incoming_message, 'sender_staff_id', '')
                logger.info(f"对象格式 - 用户: {sender_nick}, ID: {sender_id}, 内容: {content[:50] if content else '(空)'}")
            
            content = content.strip() if content else ""
            
            if not content:
                logger.info("消息内容为空，跳过")
                return AckMessage.STATUS_OK, "OK"
            
            # 处理消息（传入sender_id用于会话管理）
            reply = await asyncio.to_thread(handle_message, content, sender_nick, sender_id)
            
            if reply:
                # 根据消息类型选择回复方式
                if isinstance(incoming_message, dict):
                    # 使用ChatbotMessage对象回复
                    message = ChatbotMessage.from_dict(incoming_message)
                    self.reply_text(reply, message)
                else:
                    self.reply_text(reply, incoming_message)
                logger.info(f"已回复: {reply[:50]}...")
            
            return AckMessage.STATUS_OK, "OK"

        except Exception as e:
            logger.exception(f"处理消息异常: {e}")
            return AckMessage.STATUS_OK, "OK"


# ============== 启动 ==============

def check_single_instance():
    """确保只有一个实例运行（通过锁文件）"""
    import sys
    import os
    
    lock_file = Path(__file__).parent / ".bot.lock"
    
    # 检查锁文件
    if lock_file.exists():
        try:
            with open(lock_file, "r") as f:
                old_pid = int(f.read().strip())
            
            # 检查进程是否还在运行
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {old_pid}"],
                capture_output=True, text=True
            )
            if str(old_pid) in result.stdout:
                print(f"[ERROR] 机器人已在运行中 (PID: {old_pid})")
                print("如需重启，请先关闭现有进程")
                sys.exit(1)
        except (ValueError, FileNotFoundError):
            pass  # 锁文件损坏或进程已不存在，可以继续
    
    # 写入当前PID
    with open(lock_file, "w") as f:
        f.write(str(os.getpid()))
    
    # 注册退出时清理锁文件
    import atexit
    def cleanup():
        try:
            lock_file.unlink()
        except:
            pass
    atexit.register(cleanup)
    
    return True


def main():
    global KB_DOCUMENTS

    # 确保单实例运行
    check_single_instance()
    
    load_config()
    KB_DOCUMENTS = load_knowledge_base()

    print("=" * 50)
    print("斯坦星球知识库钉钉机器人 (Stream模式)")
    print(f"已加载 {len(KB_DOCUMENTS)} 个文档")
    print(f"进程PID: {__import__('os').getpid()}")
    print("=" * 50)
    print("\n支持私聊和群聊")
    print("按 Ctrl+C 停止服务\n")

    # 创建Stream客户端
    credential = dingtalk_stream.Credential(
        CONFIG["app_key"],
        CONFIG["app_secret"]
    )
    client = dingtalk_stream.DingTalkStreamClient(credential)

    # 注册消息处理器
    client.register_callback_handler(
        dingtalk_stream.chatbot.ChatbotMessage.TOPIC,
        StarplanetKnowledgeHandler()
    )

    # 启动
    client.start_forever()


if __name__ == "__main__":
    main()

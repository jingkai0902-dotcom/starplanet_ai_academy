#!/usr/bin/env python3
"""
斯坦星球知识库钉钉机器人 - RAG模式
使用Claude API基于知识库内容生成回答

功能：
- 课程咨询（STEM/CODE/PythonAI/C++信奥）
- 销售话术指导
- 教学问题解答
- 家长沟通建议
"""

import hashlib
import hmac
import base64
import json
import re
import logging
import threading
from pathlib import Path
from flask import Flask, request, jsonify
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============== 配置区域 ==============
CONFIG = {
    "app_key": "",           # 钉钉应用AppKey
    "app_secret": "",        # 钉钉应用AppSecret
    "agent_id": "",          # 钉钉机器人AgentID
    "kb_path": "",           # 知识库JSON文件目录
    "llm_provider": "zhipu",
    "llm_api_key": "",       # 大模型API密钥
    "llm_base_url": "https://open.bigmodel.cn/api/paas/v4",
    "llm_model": "glm-4.7",
    "claude_api_key": "",    # 兼容旧配置
    "claude_base_url": "",   # 兼容旧配置
}

# ============== 用户身份识别 ==============

def get_user_info(data: dict) -> dict:
    """从钉钉回调数据中提取用户信息"""
    return {
        "staff_id": data.get("senderStaffId", ""),
        "sender_nick": data.get("senderNick", ""),
        "sender_id": data.get("senderId", ""),
    }


# ============== 知识库加载与搜索 ==============

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

            # entries列表格式
            if "entries" in data:
                for entry in data["entries"]:
                    documents.append({
                        "title": entry.get("title", ""),
                        "source": json_file.name,
                        "content": entry.get("content", {}).get("raw", ""),
                        "sections": []
                    })
            # md转换的JSON格式（full_content或sections）
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
            # STEM相关
            "stem": ["stem", "幼儿", "科创", "机械", "建筑", "物理"],
            "小班": ["小班", "3-4岁", "认识我自己", "动物", "植物"],
            "中班": ["中班", "4-5岁", "机械", "建筑", "智能"],
            "大班": ["大班", "5-6岁", "复杂机械", "能源", "空间", "智能硬件"],
            # CODE相关
            "code": ["code", "scratch", "编程", "少儿编程", "游戏开发"],
            "code1": ["code1", "机械结构", "智能硬件", "编程启蒙"],
            "code2": ["code2", "智能应用", "智能交互", "算法逻辑"],
            "code3": ["code3", "智能系统", "游戏开发", "高级工程"],
            # Python相关
            "python": ["python", "pythonai", "人工智能", "ai"],
            "l1": ["l1", "函数", "算法", "数据结构"],
            "l2": ["l2", "数据科学", "计算机视觉", "cv", "仿生"],
            # C++信奥
            "信奥": ["信奥", "c++", "noi", "csp", "竞赛"],
            # 销售相关
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


# ============== Claude RAG ==============

def build_context(documents: list, max_chars: int = 8000) -> str:
    """构建上下文，控制长度"""
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


def get_llm_config():
    """获取大模型配置（优先读取llm_*, 兼容claude_*）"""
    api_key = CONFIG.get("llm_api_key") or CONFIG.get("claude_api_key") or ""
    base_url = CONFIG.get("llm_base_url") or CONFIG.get("claude_base_url") or "https://open.bigmodel.cn/api/paas/v4"
    model = CONFIG.get("llm_model") or "glm-4.7"
    return api_key, base_url, model


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
        return content.strip()
    except Exception as e:
        logger.error(f"LLM调用异常: {e}")
        return "抱歉，处理您的问题时出错了。"


def process_question(question: str, documents: list) -> str:
    """处理用户问题：搜索+生成"""
    relevant_docs = search_documents(question, documents, max_results=5)

    if not relevant_docs:
        return "抱歉，没有找到与您问题相关的内容。请尝试换个关键词，或咨询教学主管。"

    context = build_context(relevant_docs)
    answer = ask_llm(question, context)

    return answer


# ============== 钉钉接口 ==============

def verify_signature(timestamp: str, sign: str) -> bool:
    """验证钉钉请求签名"""
    if not CONFIG["app_secret"]:
        return True

    string_to_sign = f"{timestamp}\n{CONFIG['app_secret']}"
    hmac_code = hmac.new(
        CONFIG["app_secret"].encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    calculated_sign = base64.b64encode(hmac_code).decode("utf-8")

    return sign == calculated_sign


def send_message(webhook_url: str, content: str):
    """通过Webhook发送消息"""
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {"content": content}
    }

    try:
        resp = requests.post(webhook_url, json=data, headers=headers, timeout=30)
        logger.info(f"消息发送结果: {resp.status_code}")
    except Exception as e:
        logger.error(f"发送消息失败: {e}")


def handle_text_message(content: str, session_webhook: str):
    """后台处理消息并发送回复，避免回调超时"""
    try:
        reply = None

        # 帮助命令
        if content in ["帮助", "help", "?"]:
            reply = """🤖 斯坦星球知识库助手

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

💡 提示：您也可以私聊我，获得更专注的服务"""

        # 快捷命令
        elif content.startswith("/"):
            cmd = content[1:].lower()
            if cmd == "stem":
                reply = """📘 STEM幼儿科创课程（3-6岁）

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
                reply = """💻 CODE少儿编程课程（6-12岁）

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
                reply = """🐍 PythonAI课程（10岁+）

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
                reply = """💰 常见价格异议处理

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

        # 普通问答
        if reply is None:
            reply = process_question(content, KB_DOCUMENTS)

        if session_webhook:
            send_message(session_webhook, reply)
    except Exception as e:
        logger.exception(f"后台处理消息失败: {e}")


# ============== 路由 ==============

KB_DOCUMENTS = []


@app.before_request
def ensure_kb_loaded():
    """确保知识库已加载"""
    global KB_DOCUMENTS
    if not KB_DOCUMENTS:
        load_config()
        KB_DOCUMENTS = load_knowledge_base()


@app.route("/", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "斯坦星球知识库钉钉机器人(RAG+Claude)",
        "documents": len(KB_DOCUMENTS)
    })


@app.route("/dingtalk/callback", methods=["POST"])
def dingtalk_callback():
    """钉钉消息回调"""
    try:
        data = request.json
        logger.info(f"收到消息: {json.dumps(data, ensure_ascii=False)[:300]}")

        # 验证签名
        timestamp = request.headers.get("timestamp", "")
        sign = request.headers.get("sign", "")
        if CONFIG["app_secret"] and not verify_signature(timestamp, sign):
            return jsonify({"errcode": 403, "errmsg": "签名验证失败"})

        msg_type = data.get("msgtype", "")

        if msg_type == "text":
            content = data.get("text", {}).get("content", "").strip()
            session_webhook = data.get("sessionWebhook", "")

            if not content:
                return jsonify({"errcode": 0, "errmsg": "ok"})

            # 获取用户信息
            user_info = get_user_info(data)
            logger.info(f"用户: {user_info['sender_nick']}, StaffID: {user_info['staff_id']}")
            # 后台处理，避免回调超时
            if session_webhook:
                threading.Thread(
                    target=handle_text_message,
                    args=(content, session_webhook),
                    daemon=True
                ).start()

        return jsonify({"errcode": 0, "errmsg": "ok"})

    except Exception as e:
        logger.exception(f"处理回调异常: {e}")
        return jsonify({"errcode": 500, "errmsg": str(e)})


# ============== 启动 ==============

if __name__ == "__main__":
    load_config()
    KB_DOCUMENTS = load_knowledge_base()

    print("=" * 50)
    print("斯坦星球知识库钉钉机器人 (RAG + Claude)")
    print(f"已加载 {len(KB_DOCUMENTS)} 个文档")
    print("=" * 50)

    app.run(host="0.0.0.0", port=8081, debug=True)

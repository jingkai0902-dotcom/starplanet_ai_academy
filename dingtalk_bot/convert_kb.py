#!/usr/bin/env python3
"""
将斯坦星球知识库md文件转换为JSON格式，供钉钉机器人使用

使用方法：
python convert_kb.py

输出目录：dingtalk_bot/knowledge_base/

更新日期：2026-02-10
版本：V2.0 - 支持500+课程文件（单节课拆分版）
"""
import os
import json
import re
from pathlib import Path

def md_to_json(md_path):
    """将单个md文件转换为JSON格式"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else Path(md_path).stem

    # 提取章节
    sections = []
    current_section = None
    current_content = []

    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip()
        })

    return {
        'title': title,
        'source': str(md_path),
        'sections': sections,
        'full_content': content
    }

def process_directory(input_dir, output_dir, prefix=""):
    """处理目录下所有md文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    index = []
    skipped = []

    # 跳过的文件模式
    skip_patterns = ['_索引', '_总索引', 'README', 'QUICKSTART', 'NotebookLM',
                     '交付文档', '协议库', '_备份', '进度报告']

    for md_file in input_path.rglob('*.md'):
        # 跳过某些文件
        if any(p in str(md_file) for p in skip_patterns):
            skipped.append(str(md_file))
            continue

        try:
            data = md_to_json(md_file)

            # 生成输出文件名
            relative_path = md_file.relative_to(input_path)
            json_name = str(relative_path).replace('/', '_').replace('\\', '_').replace('.md', '.json')
            if prefix:
                json_name = f"{prefix}_{json_name}"
            json_path = output_path / json_name

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            index.append({
                'title': data['title'],
                'file': json_name,
                'source': str(relative_path)
            })
            print(f"[OK] {relative_path}")
        except Exception as e:
            print(f"[ERR] {md_file}: {e}")

    return index, skipped

def main():
    """主函数"""
    # 输出目录
    output_dir = Path(__file__).parent / 'knowledge_base'

    # 清空旧文件（保留_总索引.json）
    if output_dir.exists():
        for f in output_dir.glob('*.json'):
            if f.name != '_总索引.json':
                f.unlink()

    output_dir.mkdir(parents=True, exist_ok=True)

    # 知识库根目录
    kb_root = Path(__file__).parent.parent / '知识库'

    print("=" * 60)
    print("斯坦星球知识库转换工具 V2.0")
    print("=" * 60)

    all_index = []
    total_converted = 0
    total_skipped = 0

    # 需要转换的目录（按优先级排序）
    dirs_to_process = [
        # 萃取报告（核心内容）
        ('萃取报告/品牌', '品牌', 'HIGH - 品牌知识'),
        ('萃取报告/STEM', 'STEM', 'HIGH - STEM课程'),
        ('萃取报告/CODE', 'CODE', 'HIGH - CODE课程'),
        ('萃取报告/PythonAI', 'PythonAI', 'HIGH - PythonAI课程'),

        # 知识点数据库
        ('02_知识点数据库/编程概念库', '编程概念', 'MEDIUM - 编程概念'),
        ('02_知识点数据库/硬件知识库', '硬件知识', 'MEDIUM - 硬件知识'),
        ('02_知识点数据库/AI知识库', 'AI知识', 'MEDIUM - AI知识'),
        ('02_知识点数据库/机械结构库', '机械结构', 'MEDIUM - 机械结构'),
        ('02_知识点数据库/数学概念库', '数学概念', 'MEDIUM - 数学概念'),
        ('02_知识点数据库/螺旋进阶图', '螺旋进阶', 'MEDIUM - 螺旋进阶'),

        # 教师培训手册
        ('培训体系/教师培训手册', '培训手册', 'MEDIUM - 教师培训'),

        # 素材资源
        ('萃取报告', '素材', 'LOW - 素材资源'),  # 只处理根目录的素材文件
    ]

    for subdir, prefix, priority in dirs_to_process:
        full_path = kb_root / subdir
        if full_path.exists():
            print(f"\n=== [{priority}] {subdir} ===")

            # 特殊处理：萃取报告根目录只处理素材文件
            if subdir == '萃取报告' and prefix == '素材':
                # 只处理根目录的md文件，不递归
                index = []
                for md_file in full_path.glob('*.md'):
                    if '素材' in md_file.name:
                        try:
                            data = md_to_json(md_file)
                            json_name = f"{prefix}_{md_file.name.replace('.md', '.json')}"
                            json_path = output_dir / json_name
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            index.append({
                                'title': data['title'],
                                'file': json_name,
                                'source': md_file.name
                            })
                            print(f"[OK] {md_file.name}")
                        except Exception as e:
                            print(f"[ERR] {md_file}: {e}")
                all_index.extend(index)
                total_converted += len(index)
            else:
                index, skipped = process_directory(full_path, output_dir, prefix)
                all_index.extend(index)
                total_converted += len(index)
                total_skipped += len(skipped)
        else:
            print(f"[SKIP] 目录不存在: {subdir}")

    # 检查shared/knowledge_base目录（兼容旧结构）
    shared_kb = Path(__file__).parent.parent / 'shared' / 'knowledge_base'
    if shared_kb.exists():
        print(f"\n=== [LEGACY] shared/knowledge_base ===")

        legacy_dirs = [
            ('执行层专区', '执行层'),
            ('管理层专区', '管理层'),
            ('决策层专区', '决策层'),
            ('培训体系', '培训'),
        ]

        for subdir, prefix in legacy_dirs:
            full_path = shared_kb / subdir
            if full_path.exists():
                index, skipped = process_directory(full_path, output_dir, prefix)
                all_index.extend(index)
                total_converted += len(index)
                total_skipped += len(skipped)

    # 写入总索引
    with open(output_dir / '_总索引.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(all_index),
            'updated': '2026-02-10',
            'version': 'V2.0',
            'documents': all_index
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"完成！")
    print(f"  - 已转换: {total_converted} 个文件")
    print(f"  - 已跳过: {total_skipped} 个文件")
    print(f"  - 输出目录: {output_dir}")
    print("=" * 60)

    return total_converted

if __name__ == '__main__':
    main()

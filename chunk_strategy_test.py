#!/usr/bin/env python3
"""
測試不同切塊策略的效果
"""

import json
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path

def strategy_1_fixed_size(text: str, chunk_size: int = 300) -> List[str]:
    """策略1：固定大小切塊（簡單粗暴）"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

def strategy_2_sentence_aware(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """策略2：句子感知切塊（保持語義完整）"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    sentences = re.split(r'[。！？]', text)

    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence += "。"

        if len(current_chunk + sentence) <= chunk_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence if overlap == 0 else current_chunk[-overlap:] + sentence
            else:
                chunks.append(sentence[:chunk_size])
                current_chunk = sentence[chunk_size:]

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def strategy_3_semantic_sections(text: str, chunk_size: int = 450) -> List[str]:
    """策略3：語義段落切塊（基於內容結構）"""
    # 識別段落分隔符
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # 如果單個段落太長，需要進一步切分
        if len(paragraph) > chunk_size:
            # 使用句子感知方式切分長段落
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            para_chunks = strategy_2_sentence_aware(paragraph, chunk_size, 30)
            chunks.extend(para_chunks)
        else:
            # 檢查是否可以和當前 chunk 合併
            if len(current_chunk + "\n" + paragraph) <= chunk_size:
                current_chunk += "\n" + paragraph if current_chunk else paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def strategy_4_content_aware(text: str, chunk_size: int = 500) -> List[str]:
    """策略4：內容感知切塊（針對財經新聞優化）"""
    # 財經新聞的特殊標記
    financial_markers = [
        r'[股票代碼|證券代碼][:：]\s*\d+',
        r'收盤價|開盤價|最高價|最低價',
        r'漲跌[幅度]*[:：]',
        r'成交量|成交額',
        r'市值|淨值|本益比|股價淨值比',
        r'營收|獲利|EPS|ROE|ROA',
        r'分析師|投資建議|目標價',
        r'風險[提醒|警示|評估]',
    ]

    chunks = []

    # 先按段落分割
    paragraphs = text.split('\n')
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 檢查是否包含重要財經信息
        has_financial_info = any(re.search(pattern, para) for pattern in financial_markers)

        # 如果包含重要財經信息，優先保持完整
        if has_financial_info and len(para) <= chunk_size * 1.2:  # 允許稍微超出
            if len(current_chunk + "\n" + para) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n" + para if current_chunk else para
        else:
            # 普通段落按標準規則處理
            if len(current_chunk + "\n" + para) <= chunk_size:
                current_chunk += "\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 如果段落太長，使用句子感知切分
                if len(para) > chunk_size:
                    para_chunks = strategy_2_sentence_aware(para, chunk_size, 30)
                    chunks.extend(para_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def strategy_5_hierarchical(text: str, min_chunk: int = 200, max_chunk: int = 600) -> List[str]:
    """策略5：階層式切塊（動態調整大小）"""
    # 檢測文本類型和重要性
    def get_content_importance(content: str) -> float:
        financial_keywords = ['投資', '股票', '市場', '分析', '建議', '風險', '報酬', '價格']
        importance = sum(1 for keyword in financial_keywords if keyword in content)
        return min(importance / len(financial_keywords), 1.0)

    chunks = []
    sentences = re.split(r'[。！？]', text)

    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence += "。"
        importance = get_content_importance(sentence)

        # 根據重要性動態調整目標大小
        target_size = min_chunk + int((max_chunk - min_chunk) * importance)

        if len(current_chunk + sentence) <= target_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def analyze_chunk_quality(chunks: List[str], strategy_name: str) -> Dict[str, Any]:
    """分析切塊質量"""
    if not chunks:
        return {"strategy": strategy_name, "error": "No chunks generated"}

    chunk_lengths = [len(chunk) for chunk in chunks]

    # 檢查語義完整性（簡單指標）
    incomplete_chunks = sum(1 for chunk in chunks if not chunk.strip().endswith(('。', '！', '？', ':', '：')))

    # 檢查信息密度
    financial_keywords = ['投資', '股票', '市場', '分析', '建議', '風險', '報酬', '價格', '收盤', '開盤']
    avg_keywords_per_chunk = sum(
        sum(1 for keyword in financial_keywords if keyword in chunk)
        for chunk in chunks
    ) / len(chunks)

    return {
        "strategy": strategy_name,
        "total_chunks": len(chunks),
        "avg_length": sum(chunk_lengths) / len(chunks),
        "min_length": min(chunk_lengths),
        "max_length": max(chunk_lengths),
        "length_std": (sum((l - sum(chunk_lengths)/len(chunks))**2 for l in chunk_lengths) / len(chunks))**0.5,
        "incomplete_chunks": incomplete_chunks,
        "completeness_rate": (len(chunks) - incomplete_chunks) / len(chunks),
        "avg_keywords_per_chunk": avg_keywords_per_chunk,
        "information_density": avg_keywords_per_chunk / (sum(chunk_lengths) / len(chunks) / 100)  # 每100字符的關鍵字密度
    }

def test_all_strategies():
    """測試所有切塊策略"""
    # 載入測試數據
    data_file = Path(__file__).parent / "data" / "real_cnyes_news_20250927_132114.json"

    if not data_file.exists():
        print(f"測試數據文件不存在: {data_file}")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    if not articles:
        print("沒有找到文章數據")
        return

    print("=== 切塊策略效果分析 ===\n")

    # 選擇一篇代表性文章進行測試
    test_article = articles[0]  # 選擇第一篇文章
    title = test_article.get('title', '')
    content = test_article.get('content', '')
    category = test_article.get('category', '')

    full_text = f"標題：{title}\n分類：{category}\n內容：{content}"

    print(f"測試文章：{title[:50]}...")
    print(f"原文長度：{len(full_text)} 字符\n")

    strategies = [
        ("固定大小切塊", lambda t: strategy_1_fixed_size(t, 300)),
        ("句子感知切塊", lambda t: strategy_2_sentence_aware(t, 400, 50)),
        ("語義段落切塊", lambda t: strategy_3_semantic_sections(t, 450)),
        ("內容感知切塊", lambda t: strategy_4_content_aware(t, 500)),
        ("階層式切塊", lambda t: strategy_5_hierarchical(t, 200, 600))
    ]

    results = []

    for strategy_name, strategy_func in strategies:
        print(f"--- {strategy_name} ---")

        try:
            chunks = strategy_func(full_text)
            analysis = analyze_chunk_quality(chunks, strategy_name)
            results.append(analysis)

            print(f"塊數量: {analysis['total_chunks']}")
            print(f"平均長度: {analysis['avg_length']:.1f} 字符")
            print(f"長度範圍: {analysis['min_length']}-{analysis['max_length']}")
            print(f"完整性: {analysis['completeness_rate']:.1%}")
            print(f"信息密度: {analysis['information_density']:.3f}")
            print(f"示例塊: {chunks[0][:100]}...")
            print()

        except Exception as e:
            print(f"策略執行失敗: {e}")
            print()

    # 總結最佳策略
    print("=== 策略排名 ===")

    # 綜合評分（完整性 40% + 信息密度 40% + 塊數量適中 20%）
    for result in results:
        if 'error' not in result:
            completeness_score = result['completeness_rate']
            density_score = min(result['information_density'] / 0.1, 1.0)  # 正規化到0-1
            chunk_count_score = 1.0 / (1.0 + abs(result['total_chunks'] - 5) * 0.1)  # 理想塊數約5個

            final_score = (completeness_score * 0.4 +
                          density_score * 0.4 +
                          chunk_count_score * 0.2)

            result['final_score'] = final_score

    # 排序並顯示結果
    valid_results = [r for r in results if 'error' not in r]
    valid_results.sort(key=lambda x: x['final_score'], reverse=True)

    for i, result in enumerate(valid_results, 1):
        print(f"{i}. {result['strategy']} - 總分: {result['final_score']:.3f}")
        print(f"   完整性: {result['completeness_rate']:.1%}, 信息密度: {result['information_density']:.3f}")

    print(f"\n🏆 推薦策略: {valid_results[0]['strategy']}")

    return valid_results[0]['strategy']

if __name__ == "__main__":
    best_strategy = test_all_strategies()
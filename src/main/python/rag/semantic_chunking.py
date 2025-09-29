"""
語意邊界切割系統

基於句子間語意相似度檢測，在語意轉換點進行切割
實現真正的語意感知文檔分段，提升 RAG 檢索精度
"""

import re
import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import openai
from sentence_transformers import SentenceTransformer
import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class SemanticChunk:
    """語意切割片段"""
    text: str
    start_sentence_idx: int
    end_sentence_idx: int
    core_start_idx: int  # 非重疊部分開始
    overlap_length: int = 0
    boundary_confidence: float = 0.0
    semantic_coherence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkingConfig:
    """切割配置參數"""
    # 大小限制
    min_chunk_size: int = 200
    max_chunk_size: int = 800
    target_chunk_size: int = 500

    # 語意邊界檢測
    similarity_threshold: float = 0.75
    boundary_confidence_threshold: float = 0.6
    min_sentences_per_chunk: int = 2

    # 重疊策略
    overlap_sentences: int = 2
    overlap_ratio: float = 0.15  # 最大重疊比例

    # Embedding 配置
    embedding_model: str = "openai"  # "openai" or "local"
    openai_model: str = "text-embedding-3-small"
    local_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # 財經優化
    enable_financial_optimization: bool = True
    transition_penalty: float = 0.8  # 轉折詞相似度懲罰
    data_continuity_bonus: float = 1.2  # 數據連續性加成


class EmbeddingService:
    """Embedding 服務封裝"""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.openai_client = None
        self.local_model = None
        self.tokenizer = None

        self._initialize_service()

    def _initialize_service(self):
        """初始化 Embedding 服務"""
        if self.config.embedding_model == "openai":
            try:
                self.openai_client = openai.OpenAI()
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
                logger.info("OpenAI Embedding service initialized")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}, falling back to local model")
                self.config.embedding_model = "local"

        if self.config.embedding_model == "local":
            try:
                self.local_model = SentenceTransformer(self.config.local_model)
                logger.info(f"Local embedding model loaded: {self.config.local_model}")
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")
                raise

    async def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """計算文本 embeddings"""
        if not texts:
            return np.array([])

        if self.config.embedding_model == "openai" and self.openai_client:
            return await self._compute_openai_embeddings(texts)
        else:
            return self._compute_local_embeddings(texts)

    async def _compute_openai_embeddings(self, texts: List[str]) -> np.ndarray:
        """使用 OpenAI API 計算 embeddings"""
        try:
            # 批次處理，避免超過 API 限制
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]

                # 檢查 token 長度並截斷過長文本
                processed_texts = []
                for text in batch_texts:
                    tokens = self.tokenizer.encode(text)
                    if len(tokens) > 8000:  # 保留安全邊界
                        truncated_tokens = tokens[:8000]
                        text = self.tokenizer.decode(truncated_tokens)
                    processed_texts.append(text)

                response = await asyncio.to_thread(
                    self.openai_client.embeddings.create,
                    model=self.config.openai_model,
                    input=processed_texts
                )

                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

                # 避免 API 頻率限制
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)

            return np.array(all_embeddings)

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            # 降級到本地模型
            logger.info("Falling back to local embedding model")
            return self._compute_local_embeddings(texts)

    def _compute_local_embeddings(self, texts: List[str]) -> np.ndarray:
        """使用本地模型計算 embeddings"""
        try:
            embeddings = self.local_model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Local embedding failed: {e}")
            raise


class SemanticBoundaryDetector:
    """語意邊界檢測器"""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.embedding_service = EmbeddingService(config)

        # 財經內容優化關鍵詞
        self.financial_transitions = [
            '然而', '但是', '不過', '相反地', '另一方面', '相對而言',
            '此外', '同時', '另外', '除此之外', '值得注意的是',
            '因此', '所以', '總之', '綜合來看', '整體而言',
            '需要強調的是', '重要的是', '關鍵在於'
        ]

        self.financial_data_indicators = [
            '營收', '獲利', 'EPS', '股價', '市值', '淨利',
            '第一季', '第二季', '第三季', '第四季', 'Q1', 'Q2', 'Q3', 'Q4',
            '去年同期', '較前期', '年增率', '季增率', '同比', '環比',
            '毛利率', '營業利益', '稅後淨利', '每股盈餘',
            '收盤價', '開盤價', '最高價', '最低價', '成交量'
        ]

    def extract_sentences(self, text: str) -> List[str]:
        """提取句子，保持合理的句子邊界"""
        # 使用更精確的中文句子分割
        sentence_endings = r'[。！？；]'
        potential_sentences = re.split(f'({sentence_endings})', text)

        sentences = []
        current_sentence = ""

        for i, part in enumerate(potential_sentences):
            if re.match(sentence_endings, part):
                # 這是標點符號，加到當前句子
                current_sentence += part
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                # 這是文本內容
                current_sentence += part

        # 處理最後一個句子（可能沒有標點）
        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        # 過濾過短的句子並合併
        filtered_sentences = []
        for sentence in sentences:
            if len(sentence) < 10 and filtered_sentences:
                # 短句合併到前一句
                filtered_sentences[-1] += sentence
            elif len(sentence) >= 5:  # 最小句子長度
                filtered_sentences.append(sentence)

        return filtered_sentences

    async def detect_boundaries(self, text: str) -> Tuple[List[int], List[float]]:
        """
        檢測語意邊界

        Returns:
            boundaries: 邊界位置列表 (句子索引)
            confidences: 各邊界的信心度
        """
        sentences = self.extract_sentences(text)

        if len(sentences) <= self.config.min_sentences_per_chunk:
            return [0, len(sentences)], [1.0, 1.0]

        # 計算句子 embeddings
        embeddings = await self.embedding_service.compute_embeddings(sentences)

        if embeddings.size == 0:
            logger.warning("No embeddings computed, using fallback chunking")
            return self._fallback_boundaries(sentences), [0.5] * len(sentences)

        # 計算相鄰句子相似度
        similarities = self._calculate_similarities(embeddings)

        # 財經內容優化
        if self.config.enable_financial_optimization:
            similarities = self._apply_financial_optimization(similarities, sentences)

        # 檢測候選邊界
        candidate_boundaries = self._find_candidate_boundaries(similarities)

        # 基於大小約束優化邊界
        final_boundaries, confidences = self._optimize_boundaries(
            candidate_boundaries, sentences, similarities
        )

        return final_boundaries, confidences

    def _calculate_similarities(self, embeddings: np.ndarray) -> List[float]:
        """計算相鄰句子的餘弦相似度"""
        similarities = []

        for i in range(len(embeddings) - 1):
            vec1 = embeddings[i]
            vec2 = embeddings[i + 1]

            # 餘弦相似度計算
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm1 * norm2)

            similarities.append(float(similarity))

        return similarities

    def _apply_financial_optimization(self, similarities: List[float],
                                    sentences: List[str]) -> List[float]:
        """應用財經內容特定優化"""
        enhanced_similarities = similarities.copy()

        for i in range(len(sentences) - 1):
            current_sentence = sentences[i]
            next_sentence = sentences[i + 1]

            # 檢測轉折詞 - 降低相似度，鼓勵切割
            has_transition = any(
                marker in next_sentence for marker in self.financial_transitions
            )
            if has_transition:
                enhanced_similarities[i] *= self.config.transition_penalty
                logger.debug(f"Applied transition penalty at sentence {i}")

            # 檢測數據連續性 - 提高相似度，避免切割
            current_has_data = any(
                indicator in current_sentence for indicator in self.financial_data_indicators
            )
            next_has_data = any(
                indicator in next_sentence for indicator in self.financial_data_indicators
            )

            if current_has_data and next_has_data:
                enhanced_similarities[i] *= self.config.data_continuity_bonus
                enhanced_similarities[i] = min(enhanced_similarities[i], 1.0)
                logger.debug(f"Applied data continuity bonus at sentence {i}")

        return enhanced_similarities

    def _find_candidate_boundaries(self, similarities: List[float]) -> List[Tuple[int, float]]:
        """找到候選邊界點"""
        candidates = []

        # 找到相似度低點
        for i in range(1, len(similarities) - 1):
            current_sim = similarities[i]

            # 檢查是否為局部最小值且低於閾值
            is_local_minimum = (
                current_sim < similarities[i - 1] and
                current_sim < similarities[i + 1]
            )

            below_threshold = current_sim < self.config.similarity_threshold

            if is_local_minimum and below_threshold:
                # 計算邊界信心度
                confidence = self._calculate_boundary_confidence(similarities, i)
                candidates.append((i + 1, confidence))  # +1 因為這是下一個句子的開始

        # 按信心度排序
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates

    def _calculate_boundary_confidence(self, similarities: List[float],
                                     position: int) -> float:
        """計算邊界信心度"""
        current_sim = similarities[position]

        # 基礎信心度：1 - 相似度
        base_confidence = 1.0 - current_sim

        # 考慮周圍的相似度變化
        window_size = 2
        left_start = max(0, position - window_size)
        right_end = min(len(similarities), position + window_size + 1)

        surrounding_sims = similarities[left_start:right_end]
        avg_surrounding = np.mean(surrounding_sims)

        # 相對下降幅度
        relative_drop = (avg_surrounding - current_sim) / (avg_surrounding + 1e-6)

        # 最終信心度
        final_confidence = base_confidence * (1 + relative_drop)

        return min(1.0, max(0.0, final_confidence))

    def _optimize_boundaries(self, candidates: List[Tuple[int, float]],
                           sentences: List[str],
                           similarities: List[float]) -> Tuple[List[int], List[float]]:
        """基於大小約束優化邊界"""
        if not candidates:
            return self._fallback_boundaries(sentences), [0.5] * len(sentences)

        final_boundaries = [0]  # 總是從第0個句子開始
        confidences = [1.0]

        current_start = 0

        for boundary_pos, confidence in candidates:
            # 計算當前 chunk 的大小
            current_chunk_text = ''.join(sentences[current_start:boundary_pos])
            current_size = len(current_chunk_text)

            # 檢查大小約束
            if current_size >= self.config.min_chunk_size:
                # 檢查是否需要強制切割（超過最大大小）
                if current_size > self.config.max_chunk_size:
                    # 強制切割，但優先選擇信心度較高的邊界
                    final_boundaries.append(boundary_pos)
                    confidences.append(confidence)
                    current_start = boundary_pos
                elif confidence >= self.config.boundary_confidence_threshold:
                    # 滿足信心度要求，可以切割
                    final_boundaries.append(boundary_pos)
                    confidences.append(confidence)
                    current_start = boundary_pos

            # 如果當前 chunk 太大，必須強制切割
            elif current_size > self.config.max_chunk_size:
                final_boundaries.append(boundary_pos)
                confidences.append(max(0.3, confidence))  # 降低強制切割的信心度
                current_start = boundary_pos

        # 確保最後一個邊界
        if current_start < len(sentences):
            final_boundaries.append(len(sentences))
            confidences.append(1.0)

        return final_boundaries, confidences

    def _fallback_boundaries(self, sentences: List[str]) -> List[int]:
        """降級邊界策略"""
        # 基於目標大小的簡單切割
        boundaries = [0]
        current_size = 0

        for i, sentence in enumerate(sentences):
            current_size += len(sentence)

            if (current_size >= self.config.target_chunk_size and
                i - boundaries[-1] >= self.config.min_sentences_per_chunk):
                boundaries.append(i + 1)
                current_size = 0

        if boundaries[-1] != len(sentences):
            boundaries.append(len(sentences))

        return boundaries


class SemanticChunker:
    """語意切割主類"""

    def __init__(self, config: ChunkingConfig = None):
        self.config = config or ChunkingConfig()
        self.boundary_detector = SemanticBoundaryDetector(self.config)

    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[SemanticChunk]:
        """
        執行語意切割

        Args:
            text: 待切割文本
            metadata: 額外元數據

        Returns:
            語意切割片段列表
        """
        if not text.strip():
            return []

        # 提取句子
        sentences = self.boundary_detector.extract_sentences(text)

        if len(sentences) <= 1:
            return [SemanticChunk(
                text=text,
                start_sentence_idx=0,
                end_sentence_idx=len(sentences),
                core_start_idx=0,
                metadata=metadata or {}
            )]

        # 檢測語意邊界
        boundaries, confidences = await self.boundary_detector.detect_boundaries(text)

        # 創建切割片段
        chunks = self._create_chunks_with_overlap(
            sentences, boundaries, confidences, metadata or {}
        )

        # 計算語意一致性
        await self._calculate_semantic_coherence(chunks)

        return chunks

    def _create_chunks_with_overlap(self, sentences: List[str],
                                  boundaries: List[int],
                                  confidences: List[float],
                                  metadata: Dict[str, Any]) -> List[SemanticChunk]:
        """創建帶重疊的切割片段"""
        chunks = []

        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            confidence = confidences[i] if i < len(confidences) else 0.5

            # 計算重疊
            overlap_start = self._calculate_overlap_start(
                start_idx, i, boundaries, sentences
            )

            # 創建片段文本
            chunk_sentences = sentences[overlap_start:end_idx]
            chunk_text = ''.join(chunk_sentences)

            # 計算重疊長度
            overlap_length = start_idx - overlap_start if i > 0 else 0

            chunk = SemanticChunk(
                text=chunk_text,
                start_sentence_idx=overlap_start,
                end_sentence_idx=end_idx,
                core_start_idx=start_idx,
                overlap_length=overlap_length,
                boundary_confidence=confidence,
                metadata={
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(boundaries) - 1,
                    'sentence_count': len(chunk_sentences),
                    'core_sentence_count': end_idx - start_idx
                }
            )

            chunks.append(chunk)

        return chunks

    def _calculate_overlap_start(self, start_idx: int, chunk_idx: int,
                               boundaries: List[int], sentences: List[str]) -> int:
        """計算重疊開始位置"""
        if chunk_idx == 0:
            return start_idx

        # 基於句子數量的重疊
        sentence_overlap = min(self.config.overlap_sentences, start_idx)

        # 基於比例的重疊限制
        prev_chunk_size = start_idx - boundaries[chunk_idx - 1]
        max_overlap_by_ratio = int(prev_chunk_size * self.config.overlap_ratio)

        # 取較小值
        actual_overlap = min(sentence_overlap, max_overlap_by_ratio)

        return max(0, start_idx - actual_overlap)

    async def _calculate_semantic_coherence(self, chunks: List[SemanticChunk]):
        """計算每個片段的語意一致性"""
        for chunk in chunks:
            sentences = self.boundary_detector.extract_sentences(chunk.text)

            if len(sentences) <= 1:
                chunk.semantic_coherence = 1.0
                continue

            try:
                embeddings = await self.boundary_detector.embedding_service.compute_embeddings(sentences)

                if embeddings.size == 0:
                    chunk.semantic_coherence = 0.5
                    continue

                # 計算句子間的平均相似度
                similarities = []
                for i in range(len(embeddings) - 1):
                    sim = np.dot(embeddings[i], embeddings[i + 1]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1]) + 1e-6
                    )
                    similarities.append(float(sim))

                chunk.semantic_coherence = float(np.mean(similarities))

            except Exception as e:
                logger.warning(f"Failed to calculate semantic coherence: {e}")
                chunk.semantic_coherence = 0.5
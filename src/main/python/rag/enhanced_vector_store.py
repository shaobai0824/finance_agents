"""
增強型向量存儲

集成語意切割功能到現有的 ChromaVectorStore
提供向後兼容性和 A/B 測試支持
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import hashlib
import json

from .chroma_vector_store import ChromaVectorStore
from .semantic_chunking import SemanticChunker, SemanticChunk
from .chunking_config import ConfigManager, get_config

logger = logging.getLogger(__name__)


class EnhancedVectorStore(ChromaVectorStore):
    """
    增強型向量存儲

    在原有 ChromaVectorStore 基礎上加入語意切割功能
    支持新舊切割方式的 A/B 測試
    """

    def __init__(self,
                 collection_name: str = "finance_knowledge_semantic",
                 persist_directory: Optional[str] = None,
                 config_path: Optional[str] = None,
                 enable_semantic_chunking: bool = True,
                 fallback_to_legacy: bool = True):
        """
        初始化增強型向量存儲

        Args:
            collection_name: ChromaDB 集合名稱
            persist_directory: 持久化目錄
            config_path: 語意切割配置檔案路徑
            enable_semantic_chunking: 是否啟用語意切割
            fallback_to_legacy: 語意切割失敗時是否降級到原有方式
        """

        # 初始化父類
        super().__init__(persist_directory, collection_name)

        # 配置管理
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()

        # 語意切割器
        self.enable_semantic_chunking = enable_semantic_chunking
        self.fallback_to_legacy = fallback_to_legacy
        self.semantic_chunker = None

        if self.enable_semantic_chunking:
            try:
                # 從配置創建 ChunkingConfig 實例
                from .semantic_chunking import ChunkingConfig
                chunking_config = self._convert_to_chunking_config()
                self.semantic_chunker = SemanticChunker(chunking_config)
                logger.info("Semantic chunking enabled")
            except Exception as e:
                logger.error(f"Failed to initialize semantic chunker: {e}")
                if not self.fallback_to_legacy:
                    raise
                logger.info("Falling back to legacy chunking")

        # 統計資訊
        self.stats = {
            'semantic_chunks_created': 0,
            'legacy_chunks_created': 0,
            'semantic_failures': 0,
            'total_processing_time': 0.0,
            'avg_chunk_size': 0.0,
            'avg_semantic_coherence': 0.0
        }

    def _convert_to_chunking_config(self):
        """將配置管理器的配置轉換為 ChunkingConfig"""
        from .semantic_chunking import ChunkingConfig

        return ChunkingConfig(
            min_chunk_size=self.config.chunk_size.min_size,
            max_chunk_size=self.config.chunk_size.max_size,
            target_chunk_size=self.config.chunk_size.target_size,
            similarity_threshold=self.config.boundary.similarity_threshold,
            boundary_confidence_threshold=self.config.boundary.confidence_threshold,
            min_sentences_per_chunk=self.config.chunk_size.min_sentences,
            overlap_sentences=self.config.overlap.sentence_overlap,
            overlap_ratio=self.config.overlap.max_ratio,
            embedding_model=self.config.embedding.provider,
            openai_model=self.config.embedding.openai_model,
            local_model=self.config.embedding.local_model,
            enable_financial_optimization=self.config.financial.enabled,
            transition_penalty=self.config.financial.transition_penalty,
            data_continuity_bonus=self.config.financial.data_continuity_bonus
        )

    async def add_documents_with_semantic_chunking(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        use_semantic_chunking: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        使用語意切割添加文檔

        Args:
            documents: 文檔內容列表
            metadatas: 文檔元數據列表
            ids: 文檔ID列表
            use_semantic_chunking: 是否使用語意切割（None=使用配置預設）

        Returns:
            處理結果摘要
        """

        start_time = time.time()

        # 決定是否使用語意切割
        should_use_semantic = (
            use_semantic_chunking
            if use_semantic_chunking is not None
            else self.enable_semantic_chunking
        )

        if not should_use_semantic or not self.semantic_chunker:
            # 使用原有方式
            document_ids = super().add_documents(documents, metadatas, ids)
            self.stats['legacy_chunks_created'] += len(document_ids)

            return {
                'method': 'legacy',
                'total_documents': len(documents),
                'total_chunks': len(document_ids),
                'chunk_ids': document_ids,
                'processing_time': time.time() - start_time,
                'avg_chunks_per_document': len(document_ids) / len(documents) if documents else 0
            }

        # 使用語意切割
        try:
            result = await self._process_with_semantic_chunking(
                documents, metadatas, ids
            )

            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time

            return {
                **result,
                'processing_time': processing_time
            }

        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}")
            self.stats['semantic_failures'] += 1

            if self.fallback_to_legacy:
                logger.info("Falling back to legacy chunking")
                document_ids = super().add_documents(documents, metadatas, ids)
                self.stats['legacy_chunks_created'] += len(document_ids)

                return {
                    'method': 'legacy_fallback',
                    'total_documents': len(documents),
                    'total_chunks': len(document_ids),
                    'chunk_ids': document_ids,
                    'processing_time': time.time() - start_time,
                    'error': str(e)
                }
            else:
                raise

    async def _process_with_semantic_chunking(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]],
        ids: Optional[List[str]]
    ) -> Dict[str, Any]:
        """使用語意切割處理文檔"""

        all_chunks = []
        all_chunk_metadatas = []
        all_chunk_ids = []

        # 準備元數據
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]

        # 準備文檔ID
        if ids is None:
            ids = [self._generate_document_id(doc) for doc in documents]

        total_chunks = 0
        total_coherence = 0.0
        chunk_sizes = []

        # 處理每個文檔
        for doc_idx, (document, metadata, doc_id) in enumerate(zip(documents, metadatas, ids)):
            try:
                # 執行語意切割
                semantic_chunks = await self.semantic_chunker.chunk_text(
                    document,
                    {**metadata, 'original_document_id': doc_id}
                )

                # 處理切割結果
                for chunk_idx, chunk in enumerate(semantic_chunks):
                    chunk_id = f"{doc_id}_semantic_{chunk_idx}"

                    # 構建chunk元數據
                    chunk_metadata = {
                        **metadata,
                        'original_document_id': doc_id,
                        'chunk_index': chunk_idx,
                        'total_chunks_in_document': len(semantic_chunks),
                        'chunking_method': 'semantic',
                        'boundary_confidence': chunk.boundary_confidence,
                        'semantic_coherence': chunk.semantic_coherence,
                        'overlap_length': chunk.overlap_length,
                        'core_start_idx': chunk.core_start_idx,
                        'sentence_count': chunk.metadata.get('sentence_count', 0),
                        'processing_timestamp': datetime.now().isoformat()
                    }

                    all_chunks.append(chunk.text)
                    all_chunk_metadatas.append(chunk_metadata)
                    all_chunk_ids.append(chunk_id)

                    # 統計資訊
                    chunk_sizes.append(len(chunk.text))
                    total_coherence += chunk.semantic_coherence
                    total_chunks += 1

                logger.debug(f"Document {doc_idx} chunked into {len(semantic_chunks)} semantic chunks")

            except Exception as e:
                logger.error(f"Failed to process document {doc_idx} with semantic chunking: {e}")

                if self.fallback_to_legacy:
                    # 對這個文檔使用原有切割方式
                    legacy_chunks = self._legacy_chunk_document(document)

                    for chunk_idx, chunk_text in enumerate(legacy_chunks):
                        chunk_id = f"{doc_id}_legacy_{chunk_idx}"
                        chunk_metadata = {
                            **metadata,
                            'original_document_id': doc_id,
                            'chunk_index': chunk_idx,
                            'total_chunks_in_document': len(legacy_chunks),
                            'chunking_method': 'legacy_fallback',
                            'processing_timestamp': datetime.now().isoformat()
                        }

                        all_chunks.append(chunk_text)
                        all_chunk_metadatas.append(chunk_metadata)
                        all_chunk_ids.append(chunk_id)
                        chunk_sizes.append(len(chunk_text))
                        total_chunks += 1
                else:
                    raise

        # 批次添加到向量存儲
        if all_chunks:
            final_chunk_ids = super().add_documents(
                all_chunks,
                all_chunk_metadatas,
                all_chunk_ids
            )
        else:
            final_chunk_ids = []

        # 更新統計
        self.stats['semantic_chunks_created'] += total_chunks
        if chunk_sizes:
            self.stats['avg_chunk_size'] = sum(chunk_sizes) / len(chunk_sizes)
        if total_chunks > 0:
            self.stats['avg_semantic_coherence'] = total_coherence / total_chunks

        return {
            'method': 'semantic',
            'total_documents': len(documents),
            'total_chunks': total_chunks,
            'chunk_ids': final_chunk_ids,
            'avg_chunks_per_document': total_chunks / len(documents) if documents else 0,
            'avg_chunk_size': self.stats['avg_chunk_size'],
            'avg_semantic_coherence': self.stats['avg_semantic_coherence'],
            'chunk_size_range': f"{min(chunk_sizes)}-{max(chunk_sizes)}" if chunk_sizes else "0-0"
        }

    def _legacy_chunk_document(self, document: str, chunk_size: int = 400) -> List[str]:
        """使用原有方式切割文檔（降級使用）"""
        if len(document) <= chunk_size:
            return [document]

        chunks = []
        start = 0

        while start < len(document):
            end = start + chunk_size

            # 尋找適當的切割點（句號、問號、驚嘆號）
            if end < len(document):
                # 向後查找句號
                for i in range(end, max(start + chunk_size // 2, start), -1):
                    if document[i] in '。！？':
                        end = i + 1
                        break

            chunk = document[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end

        return chunks

    def search_with_context_expansion(
        self,
        query: str,
        n_results: int = 5,
        include_article_context: bool = True,
        max_chunks_per_article: int = 3,
        context_similarity_threshold: float = 0.3,
        chunking_method_filter: Optional[str] = None,
        min_coherence: Optional[float] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        帶文章上下文擴展的智能檢索

        Args:
            query: 搜尋查詢
            n_results: 基本檢索結果數量
            include_article_context: 是否包含同篇文章的其他chunks
            max_chunks_per_article: 每篇文章最多返回的chunks數量
            context_similarity_threshold: 上下文chunks的最低相似度閾值
            chunking_method_filter: 切割方式過濾
            min_coherence: 最小語意一致性閾值
            include_metadata: 是否包含詳細元數據

        Returns:
            擴展後的搜尋結果列表
        """

        # 1. 執行基本檢索
        primary_results = self.search_with_metadata_filtering(
            query, n_results, chunking_method_filter, min_coherence, include_metadata
        )

        if not include_article_context or not primary_results:
            return primary_results

        # 2. 文章上下文擴展
        expanded_results = []
        processed_articles = set()

        for result in primary_results:
            article_id = result.get('metadata', {}).get('original_document_id')

            if not article_id or article_id in processed_articles:
                expanded_results.append(result)
                continue

            # 獲取同篇文章的其他chunks
            article_chunks = self._get_article_chunks_with_relevance(
                article_id, query, max_chunks_per_article, context_similarity_threshold
            )

            # 將主要結果標記為primary
            result['chunk_role'] = 'primary'
            result['article_total_chunks'] = len(article_chunks)
            expanded_results.append(result)

            # 添加上下文chunks
            for chunk in article_chunks:
                if chunk['chunk_id'] != result.get('chunk_id'):  # 避免重複
                    chunk['chunk_role'] = 'context'
                    chunk['related_to_primary'] = result.get('chunk_id', 'unknown')
                    expanded_results.append(chunk)

            processed_articles.add(article_id)

        return expanded_results

    def search_with_metadata_filtering(
        self,
        query: str,
        n_results: int = 5,
        chunking_method_filter: Optional[str] = None,
        min_coherence: Optional[float] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        帶元數據過濾的搜尋

        Args:
            query: 搜尋查詢
            n_results: 返回結果數量
            chunking_method_filter: 切割方式過濾 ('semantic', 'legacy', None)
            min_coherence: 最小語意一致性閾值
            include_metadata: 是否包含詳細元數據

        Returns:
            搜尋結果列表
        """

        # 構建where條件
        where_conditions = {}

        if chunking_method_filter:
            where_conditions['chunking_method'] = chunking_method_filter

        if min_coherence is not None:
            where_conditions['semantic_coherence'] = {"$gte": min_coherence}

        # 執行搜尋
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_conditions if where_conditions else None,
                include=['documents', 'metadatas', 'distances']
            )

            # 處理結果
            processed_results = []

            if results['documents']:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    result_item = {
                        'document': doc,
                        'distance': distance,
                        'relevance_score': max(0, 1 - distance)  # 轉換為相關性分數
                    }

                    if include_metadata:
                        result_item['metadata'] = metadata
                        result_item['chunking_method'] = metadata.get('chunking_method', 'unknown')
                        result_item['semantic_coherence'] = metadata.get('semantic_coherence', 0.0)
                        result_item['boundary_confidence'] = metadata.get('boundary_confidence', 0.0)

                    processed_results.append(result_item)

            return processed_results

        except Exception as e:
            logger.error(f"Search with filtering failed: {e}")
            # 降級到基本搜尋
            return super().search(query, n_results)

    def _get_article_chunks_with_relevance(
        self,
        article_id: str,
        query: str,
        max_chunks: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        獲取指定文章的所有chunks並計算與查詢的相關性

        Args:
            article_id: 文章ID
            query: 搜尋查詢
            max_chunks: 最大返回數量
            similarity_threshold: 相似度閾值

        Returns:
            按相關性排序的文章chunks
        """
        try:
            # 搜尋該文章的所有chunks
            article_results = self.collection.query(
                query_texts=[query],
                n_results=50,  # 獲取更多結果以確保包含所有chunks
                where={"original_document_id": article_id},
                include=['documents', 'metadatas', 'distances', 'ids']
            )

            if not article_results['documents'] or not article_results['documents'][0]:
                return []

            # 處理結果並按相關性排序
            chunks = []
            for i, (doc, metadata, distance, chunk_id) in enumerate(zip(
                article_results['documents'][0],
                article_results['metadatas'][0],
                article_results['distances'][0],
                article_results['ids'][0]
            )):
                relevance_score = max(0, 1 - distance)

                # 過濾低相關性的chunks
                if relevance_score >= similarity_threshold:
                    chunk_info = {
                        'document': doc,
                        'metadata': metadata,
                        'relevance_score': relevance_score,
                        'distance': distance,
                        'chunk_id': chunk_id,
                        'chunk_index': metadata.get('chunk_index', 0),
                        'chunking_method': metadata.get('chunking_method', 'unknown'),
                        'semantic_coherence': metadata.get('semantic_coherence', 0.0),
                        'boundary_confidence': metadata.get('boundary_confidence', 0.0)
                    }
                    chunks.append(chunk_info)

            # 按相關性分數排序，但也考慮chunk在文章中的順序
            chunks.sort(key=lambda x: (
                -x['relevance_score'],  # 相關性降序
                x['chunk_index']        # 順序升序（相關性相同時保持原順序）
            ))

            return chunks[:max_chunks]

        except Exception as e:
            logger.error(f"Failed to get article chunks for {article_id}: {e}")
            return []

    def get_article_context(
        self,
        article_id: str,
        include_all_chunks: bool = False,
        sort_by_order: bool = True
    ) -> Dict[str, Any]:
        """
        獲取完整的文章上下文

        Args:
            article_id: 文章ID
            include_all_chunks: 是否包含所有chunks（忽略相關性）
            sort_by_order: 是否按chunk順序排序

        Returns:
            完整的文章資訊
        """
        try:
            # 獲取該文章的所有chunks
            article_results = self.collection.get(
                where={"original_document_id": article_id},
                include=['documents', 'metadatas', 'ids']
            )

            if not article_results['documents']:
                return {"error": f"No chunks found for article {article_id}"}

            # 組織chunks資訊
            chunks = []
            article_metadata = {}

            for i, (doc, metadata, chunk_id) in enumerate(zip(
                article_results['documents'],
                article_results['metadatas'],
                article_results['ids']
            )):
                chunk_info = {
                    'chunk_id': chunk_id,
                    'chunk_index': metadata.get('chunk_index', i),
                    'document': doc,
                    'metadata': metadata,
                    'chunking_method': metadata.get('chunking_method', 'unknown'),
                    'semantic_coherence': metadata.get('semantic_coherence', 0.0),
                    'boundary_confidence': metadata.get('boundary_confidence', 0.0),
                    'overlap_length': metadata.get('overlap_length', 0)
                }
                chunks.append(chunk_info)

                # 提取文章級別的元數據
                if i == 0:
                    article_metadata = {
                        'source': metadata.get('source', 'unknown'),
                        'category': metadata.get('category', 'unknown'),
                        'total_chunks': metadata.get('total_chunks_in_document', len(chunks)),
                        'processing_timestamp': metadata.get('processing_timestamp')
                    }

            # 排序
            if sort_by_order:
                chunks.sort(key=lambda x: x['chunk_index'])

            # 重建完整文章內容（去除重疊）
            full_content = self._reconstruct_article_content(chunks)

            return {
                'article_id': article_id,
                'article_metadata': article_metadata,
                'total_chunks': len(chunks),
                'chunks': chunks,
                'full_content': full_content,
                'avg_semantic_coherence': (
                    sum(c['semantic_coherence'] for c in chunks) / len(chunks)
                    if chunks else 0
                ),
                'chunking_methods_used': list(set(c['chunking_method'] for c in chunks))
            }

        except Exception as e:
            logger.error(f"Failed to get article context for {article_id}: {e}")
            return {"error": str(e)}

    def _reconstruct_article_content(self, chunks: List[Dict[str, Any]]) -> str:
        """
        從chunks重建完整文章內容（處理重疊）

        Args:
            chunks: 按順序排列的chunks列表

        Returns:
            重建的完整內容
        """
        if not chunks:
            return ""

        # 按chunk順序排序
        sorted_chunks = sorted(chunks, key=lambda x: x['chunk_index'])

        reconstructed = ""
        last_core_end = 0

        for chunk in sorted_chunks:
            chunk_text = chunk['document']
            overlap_length = chunk.get('overlap_length', 0)
            core_start_idx = chunk.get('metadata', {}).get('core_start_idx', 0)

            if overlap_length > 0 and reconstructed:
                # 處理重疊：只添加核心部分（非重疊部分）
                # 這需要更複雜的邏輯來正確處理重疊切割
                # 目前簡化處理：如果有重疊，跳過可能重複的部分
                estimated_overlap = min(overlap_length * 50, len(chunk_text) // 3)  # 估算重疊字符數
                core_content = chunk_text[estimated_overlap:]
                reconstructed += core_content
            else:
                # 沒有重疊或是第一個chunk
                reconstructed += chunk_text

        return reconstructed

    def search_article_aware(
        self,
        query: str,
        n_results: int = 5,
        prioritize_complete_articles: bool = True,
        min_article_coverage: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        文章感知的檢索：優先返回能提供完整上下文的文章

        Args:
            query: 搜尋查詢
            n_results: 返回結果數量
            prioritize_complete_articles: 是否優先完整文章
            min_article_coverage: 最小文章覆蓋率

        Returns:
            文章感知的檢索結果
        """
        try:
            # 1. 執行基本檢索，獲取更多結果
            initial_results = self.search_with_metadata_filtering(
                query, n_results * 3, include_metadata=True
            )

            if not initial_results:
                return []

            # 2. 按文章分組
            articles_map = {}
            for result in initial_results:
                article_id = result.get('metadata', {}).get('original_document_id', 'unknown')
                if article_id not in articles_map:
                    articles_map[article_id] = []
                articles_map[article_id].append(result)

            # 3. 評估每篇文章的相關性和完整性
            article_scores = []
            for article_id, chunks in articles_map.items():
                if article_id == 'unknown':
                    continue

                # 計算文章級別的相關性分數
                avg_relevance = sum(c['relevance_score'] for c in chunks) / len(chunks)
                max_relevance = max(c['relevance_score'] for c in chunks)

                # 計算文章覆蓋率
                total_chunks_in_article = chunks[0].get('metadata', {}).get('total_chunks_in_document', len(chunks))
                coverage = len(chunks) / total_chunks_in_article if total_chunks_in_article > 0 else 0

                # 綜合評分
                if prioritize_complete_articles:
                    # 完整性權重更高
                    final_score = (avg_relevance * 0.6 + max_relevance * 0.2 + coverage * 0.2)
                else:
                    # 相關性權重更高
                    final_score = (avg_relevance * 0.4 + max_relevance * 0.4 + coverage * 0.2)

                article_scores.append({
                    'article_id': article_id,
                    'chunks': chunks,
                    'avg_relevance': avg_relevance,
                    'max_relevance': max_relevance,
                    'coverage': coverage,
                    'final_score': final_score,
                    'total_chunks': total_chunks_in_article
                })

            # 4. 排序並選擇最佳文章
            article_scores.sort(key=lambda x: x['final_score'], reverse=True)

            # 5. 構建最終結果
            final_results = []
            for article_info in article_scores[:n_results]:
                if article_info['coverage'] >= min_article_coverage or not prioritize_complete_articles:
                    # 按chunk順序排序該文章的chunks
                    sorted_chunks = sorted(article_info['chunks'], key=lambda x: x.get('metadata', {}).get('chunk_index', 0))

                    # 標記文章資訊
                    for i, chunk in enumerate(sorted_chunks):
                        chunk['article_score'] = article_info['final_score']
                        chunk['article_coverage'] = article_info['coverage']
                        chunk['chunk_role'] = 'primary' if i == 0 else 'context'
                        chunk['article_rank'] = len(final_results) // max(1, len(sorted_chunks)) + 1

                    final_results.extend(sorted_chunks)

            return final_results[:n_results]

        except Exception as e:
            logger.error(f"Article-aware search failed: {e}")
            # 降級到基本檢索
            return self.search_with_metadata_filtering(query, n_results)

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取效能統計"""
        total_chunks = self.stats['semantic_chunks_created'] + self.stats['legacy_chunks_created']

        return {
            'total_chunks_created': total_chunks,
            'semantic_chunks': self.stats['semantic_chunks_created'],
            'legacy_chunks': self.stats['legacy_chunks_created'],
            'semantic_ratio': (
                self.stats['semantic_chunks_created'] / total_chunks
                if total_chunks > 0 else 0
            ),
            'semantic_failures': self.stats['semantic_failures'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_chunk_size': self.stats['avg_chunk_size'],
            'avg_semantic_coherence': self.stats['avg_semantic_coherence'],
            'configuration_summary': self.config_manager.get_summary()
        }

    def export_chunks_analysis(self, output_path: str):
        """匯出chunks分析報告"""
        try:
            # 獲取所有chunks的統計資訊
            all_results = self.collection.get(include=['metadatas'])

            analysis = {
                'collection_name': self.collection_name,
                'total_chunks': len(all_results['ids']) if all_results['ids'] else 0,
                'generation_timestamp': datetime.now().isoformat(),
                'performance_stats': self.get_performance_stats(),
                'chunking_methods': {},
                'coherence_distribution': {},
                'chunk_size_distribution': {}
            }

            if all_results['metadatas']:
                # 分析切割方式分佈
                methods = {}
                coherences = []
                chunk_sizes = []

                for metadata in all_results['metadatas']:
                    method = metadata.get('chunking_method', 'unknown')
                    methods[method] = methods.get(method, 0) + 1

                    coherence = metadata.get('semantic_coherence', 0.0)
                    if coherence > 0:
                        coherences.append(coherence)

                    # 估算chunk大小（基於典型字符數）
                    sentence_count = metadata.get('sentence_count', 1)
                    estimated_size = sentence_count * 50  # 估算每句50字符
                    chunk_sizes.append(estimated_size)

                analysis['chunking_methods'] = methods

                if coherences:
                    analysis['coherence_distribution'] = {
                        'avg': sum(coherences) / len(coherences),
                        'min': min(coherences),
                        'max': max(coherences),
                        'samples': len(coherences)
                    }

                if chunk_sizes:
                    analysis['chunk_size_distribution'] = {
                        'avg': sum(chunk_sizes) / len(chunk_sizes),
                        'min': min(chunk_sizes),
                        'max': max(chunk_sizes)
                    }

            # 保存分析報告
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            logger.info(f"Chunks analysis exported to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export chunks analysis: {e}")
            raise

    def compare_chunking_methods(self, test_documents: List[str],
                                sample_queries: List[str]) -> Dict[str, Any]:
        """
        比較不同切割方式的效果

        Args:
            test_documents: 測試文檔
            sample_queries: 測試查詢

        Returns:
            比較結果
        """

        comparison_results = {
            'test_timestamp': datetime.now().isoformat(),
            'test_documents_count': len(test_documents),
            'test_queries_count': len(sample_queries),
            'semantic_results': {},
            'legacy_results': {}
        }

        # 測試語意切割
        async def test_semantic():
            semantic_start = time.time()
            semantic_result = await self.add_documents_with_semantic_chunking(
                test_documents, use_semantic_chunking=True
            )
            semantic_time = time.time() - semantic_start

            # 測試檢索效果
            semantic_search_results = []
            for query in sample_queries:
                results = self.search_with_metadata_filtering(
                    query, chunking_method_filter='semantic'
                )
                avg_relevance = (
                    sum(r['relevance_score'] for r in results) / len(results)
                    if results else 0
                )
                semantic_search_results.append(avg_relevance)

            comparison_results['semantic_results'] = {
                'processing_time': semantic_time,
                'chunk_count': semantic_result['total_chunks'],
                'avg_relevance_score': (
                    sum(semantic_search_results) / len(semantic_search_results)
                    if semantic_search_results else 0
                ),
                'avg_chunk_size': semantic_result.get('avg_chunk_size', 0),
                'avg_coherence': semantic_result.get('avg_semantic_coherence', 0)
            }

        # 執行異步測試
        try:
            asyncio.run(test_semantic())
        except Exception as e:
            logger.error(f"Semantic chunking test failed: {e}")
            comparison_results['semantic_results'] = {'error': str(e)}

        return comparison_results
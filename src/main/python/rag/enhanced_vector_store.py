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
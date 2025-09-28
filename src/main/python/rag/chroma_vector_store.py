"""
ChromaVectorStore - ChromaDB 向量存儲實作

實作 Linus 哲學：
1. 好品味：簡潔的向量存儲介面，統一的 CRUD 操作
2. 實用主義：專注解決實際的知識檢索需求
3. Never break userspace：穩定的 API，向後兼容
4. 簡潔執念：避免複雜的配置，開箱即用
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """ChromaDB 向量存儲封裝

    提供簡潔的向量存儲操作介面
    """

    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "finance_knowledge"):
        """初始化 ChromaDB 客戶端

        Args:
            persist_directory: 持久化目錄，預設為專案根目錄下的 chroma_db
            collection_name: 集合名稱
        """
        self.collection_name = collection_name

        # 設定持久化目錄
        if persist_directory is None:
            persist_directory = self._get_default_persist_directory()

        # 確保目錄存在
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB 客戶端
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
            logger.info(f"ChromaDB initialized at: {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

        # 取得或建立集合
        self.collection = self._get_or_create_collection()

    def _get_default_persist_directory(self) -> str:
        """取得預設的持久化目錄"""
        # 從專案根目錄開始
        current_dir = Path(__file__).parent
        while current_dir.parent != current_dir:  # 直到根目錄
            if (current_dir / "CLAUDE.md").exists():  # 找到專案根目錄
                return str(current_dir / "chroma_db")
            current_dir = current_dir.parent

        # 如果找不到專案根目錄，使用當前目錄
        return str(Path.cwd() / "chroma_db")

    def _get_or_create_collection(self):
        """取得或建立集合

        Linus 哲學：好品味的初始化
        - 使用合理的預設設定
        - 避免複雜的配置選項
        """
        try:
            # 嘗試取得現有集合
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
            return collection
        except Exception:  # 捕獲所有例外，包括 NotFoundError
            # 集合不存在，建立新集合
            try:
                collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}  # 使用餘弦相似度
                )
                logger.info(f"Created new collection: {self.collection_name}")
                return collection
            except Exception as e:
                logger.error(f"Failed to create collection: {e}")
                # 如果創建失敗，嘗試獲取或創建集合
                collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Got or created collection: {self.collection_name}")
                return collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文件到向量存儲

        Args:
            documents: 文件內容清單
            metadatas: 文件元資料清單（可選）
            ids: 文件 ID 清單（可選，會自動生成）

        Returns:
            文件 ID 清單

        Linus 哲學：簡潔執念
        - 自動處理 ID 生成
        - 批次操作提升效率
        """
        if not documents:
            logger.warning("No documents provided")
            return []

        # 自動生成 ID（如果未提供）
        if ids is None:
            ids = [self._generate_document_id(doc) for doc in documents]

        # 準備元資料
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]

        try:
            # 批次添加文件
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to collection")
            return ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜尋相關文件

        Args:
            query: 查詢文字
            n_results: 返回結果數量
            where: 元資料過濾條件

        Returns:
            搜尋結果清單，每個結果包含 document, metadata, distance

        Linus 哲學：實用主義
        - 簡單的介面，複雜的實作
        - 返回結構化的搜尋結果
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            # 轉換為更友善的格式
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"][0] else {},
                        "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] else 1.0,
                        "id": results["ids"][0][i]
                    }
                    formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_similar_documents(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """取得相似文件（基於相似度閾值）

        Args:
            query: 查詢文字
            similarity_threshold: 相似度閾值（0-1）
            max_results: 最大結果數

        Returns:
            符合相似度閾值的文件清單
        """
        results = self.search(query, n_results=max_results)

        # 過濾相似度（ChromaDB 使用距離，需要轉換為相似度）
        similar_results = []
        for result in results:
            similarity = 1 - result["distance"]  # 距離轉相似度
            if similarity >= similarity_threshold:
                result["similarity"] = similarity
                similar_results.append(result)

        logger.info(f"Found {len(similar_results)} documents above similarity threshold {similarity_threshold}")
        return similar_results

    def update_document(self, document_id: str, document: str, metadata: Optional[Dict[str, Any]] = None):
        """更新文件"""
        try:
            update_params = {"ids": [document_id], "documents": [document]}
            if metadata:
                update_params["metadatas"] = [metadata]

            self.collection.update(**update_params)
            logger.info(f"Updated document: {document_id}")

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise

    def delete_document(self, document_id: str):
        """刪除文件"""
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document: {document_id}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """取得集合資訊"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "document_count": count,
                "persist_directory": self.client.get_settings().persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {
                "name": self.collection_name,
                "document_count": 0,
                "error": str(e)
            }

    def _generate_document_id(self, document: str) -> str:
        """生成文件 ID

        Linus 哲學：簡潔執念
        - 基於內容的 hash，確保唯一性
        - 可重現的 ID 生成
        """
        hash_object = hashlib.md5(document.encode())
        return f"doc_{hash_object.hexdigest()[:12]}"

    def clear_collection(self):
        """清空集合（謹慎使用）"""
        try:
            # 取得所有 ID
            results = self.collection.get()
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Cleared collection: {self.collection_name}")
            else:
                logger.info("Collection is already empty")

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """取得所有文件（用於除錯或備份）"""
        try:
            results = self.collection.get()
            documents = []

            if results["ids"]:
                for i in range(len(results["ids"])):
                    doc = {
                        "id": results["ids"][i],
                        "document": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    }
                    documents.append(doc)

            logger.info(f"Retrieved {len(documents)} documents from collection")
            return documents

        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            raise

    def similarity_search(self, query: str, k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[str]:
        """相似度搜尋（與 search 方法的簡化別名）

        Args:
            query: 查詢文字
            k: 返回結果數量
            where: 元資料過濾條件

        Returns:
            文檔內容清單（簡化格式）

        Note:
            這是為了與現有代碼相容而提供的別名方法
        """
        try:
            results = self.search(query, n_results=k, where=where)
            # 只返回文檔內容（簡化格式）
            documents = [result["document"] for result in results]
            logger.info(f"Similarity search found {len(documents)} results")
            return documents

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
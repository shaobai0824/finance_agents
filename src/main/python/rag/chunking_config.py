"""
語意切割配置管理系統

提供靈活的配置管理，支持環境變數、配置檔案和動態調整
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Embedding 服務配置"""
    provider: str = "openai"  # "openai" or "local"
    openai_model: str = "text-embedding-3-small"
    openai_api_key: Optional[str] = None
    local_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 100
    max_tokens: int = 8000
    rate_limit_delay: float = 0.1


@dataclass
class ChunkSizeConfig:
    """切割大小配置"""
    min_size: int = 200
    max_size: int = 800
    target_size: int = 500
    min_sentences: int = 2


@dataclass
class BoundaryConfig:
    """邊界檢測配置"""
    similarity_threshold: float = 0.75
    confidence_threshold: float = 0.6
    window_size: int = 2
    local_minimum_required: bool = True


@dataclass
class OverlapConfig:
    """重疊策略配置"""
    sentence_overlap: int = 2
    max_ratio: float = 0.15
    adaptive_overlap: bool = True


@dataclass
class FinancialOptimizationConfig:
    """財經內容優化配置"""
    enabled: bool = True
    transition_penalty: float = 0.8
    data_continuity_bonus: float = 1.2
    custom_transitions: Optional[List[str]] = None
    custom_data_indicators: Optional[List[str]] = None


@dataclass
class SemanticChunkingConfig:
    """完整的語意切割配置"""
    embedding: EmbeddingConfig = None
    chunk_size: ChunkSizeConfig = None
    boundary: BoundaryConfig = None
    overlap: OverlapConfig = None
    financial: FinancialOptimizationConfig = None

    def __post_init__(self):
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.chunk_size is None:
            self.chunk_size = ChunkSizeConfig()
        if self.boundary is None:
            self.boundary = BoundaryConfig()
        if self.overlap is None:
            self.overlap = OverlapConfig()
        if self.financial is None:
            self.financial = FinancialOptimizationConfig()

    # 全域設定
    enable_logging: bool = True
    log_level: str = "INFO"
    cache_embeddings: bool = True


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = SemanticChunkingConfig()
        self._load_configuration()

    def _load_configuration(self):
        """載入配置（優先級：環境變數 > 配置檔案 > 預設值）"""

        # 1. 載入配置檔案
        if self.config_path and Path(self.config_path).exists():
            self._load_from_file(self.config_path)
        else:
            # 嘗試載入預設配置檔案
            default_paths = [
                "semantic_chunking.yaml",
                "config/semantic_chunking.yaml",
                "src/main/resources/config/semantic_chunking.yaml"
            ]
            for path in default_paths:
                if Path(path).exists():
                    self._load_from_file(path)
                    break

        # 2. 應用環境變數覆蓋
        self._apply_env_overrides()

        # 3. 驗證配置
        self._validate_config()

        logger.info("Configuration loaded successfully")

    def _load_from_file(self, file_path: str):
        """從檔案載入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            self._update_config_from_dict(data)
            logger.info(f"Loaded configuration from {file_path}")

        except Exception as e:
            logger.warning(f"Failed to load configuration from {file_path}: {e}")

    def _update_config_from_dict(self, data: Dict[str, Any]):
        """從字典更新配置"""

        # 更新 embedding 配置
        if 'embedding' in data:
            embedding_data = data['embedding']
            for key, value in embedding_data.items():
                if hasattr(self.config.embedding, key):
                    setattr(self.config.embedding, key, value)

        # 更新切割大小配置
        if 'chunk_size' in data:
            size_data = data['chunk_size']
            for key, value in size_data.items():
                if hasattr(self.config.chunk_size, key):
                    setattr(self.config.chunk_size, key, value)

        # 更新邊界檢測配置
        if 'boundary' in data:
            boundary_data = data['boundary']
            for key, value in boundary_data.items():
                if hasattr(self.config.boundary, key):
                    setattr(self.config.boundary, key, value)

        # 更新重疊配置
        if 'overlap' in data:
            overlap_data = data['overlap']
            for key, value in overlap_data.items():
                if hasattr(self.config.overlap, key):
                    setattr(self.config.overlap, key, value)

        # 更新財經優化配置
        if 'financial' in data:
            financial_data = data['financial']
            for key, value in financial_data.items():
                if hasattr(self.config.financial, key):
                    setattr(self.config.financial, key, value)

        # 更新全域配置
        global_keys = ['enable_logging', 'log_level', 'cache_embeddings']
        for key in global_keys:
            if key in data:
                setattr(self.config, key, data[key])

    def _apply_env_overrides(self):
        """應用環境變數覆蓋"""

        # Embedding 相關
        if os.getenv('SEMANTIC_EMBEDDING_PROVIDER'):
            self.config.embedding.provider = os.getenv('SEMANTIC_EMBEDDING_PROVIDER')

        if os.getenv('SEMANTIC_OPENAI_MODEL'):
            self.config.embedding.openai_model = os.getenv('SEMANTIC_OPENAI_MODEL')

        if os.getenv('OPENAI_API_KEY'):
            self.config.embedding.openai_api_key = os.getenv('OPENAI_API_KEY')

        # 切割大小相關
        if os.getenv('SEMANTIC_MIN_CHUNK_SIZE'):
            self.config.chunk_size.min_size = int(os.getenv('SEMANTIC_MIN_CHUNK_SIZE'))

        if os.getenv('SEMANTIC_MAX_CHUNK_SIZE'):
            self.config.chunk_size.max_size = int(os.getenv('SEMANTIC_MAX_CHUNK_SIZE'))

        if os.getenv('SEMANTIC_TARGET_CHUNK_SIZE'):
            self.config.chunk_size.target_size = int(os.getenv('SEMANTIC_TARGET_CHUNK_SIZE'))

        # 邊界檢測相關
        if os.getenv('SEMANTIC_SIMILARITY_THRESHOLD'):
            self.config.boundary.similarity_threshold = float(os.getenv('SEMANTIC_SIMILARITY_THRESHOLD'))

        if os.getenv('SEMANTIC_CONFIDENCE_THRESHOLD'):
            self.config.boundary.confidence_threshold = float(os.getenv('SEMANTIC_CONFIDENCE_THRESHOLD'))

        # 財經優化相關
        if os.getenv('SEMANTIC_FINANCIAL_OPTIMIZATION'):
            self.config.financial.enabled = os.getenv('SEMANTIC_FINANCIAL_OPTIMIZATION').lower() == 'true'

        # 日誌相關
        if os.getenv('SEMANTIC_LOG_LEVEL'):
            self.config.log_level = os.getenv('SEMANTIC_LOG_LEVEL')

    def _validate_config(self):
        """驗證配置的合理性"""

        # 檢查大小配置
        if self.config.chunk_size.min_size >= self.config.chunk_size.max_size:
            raise ValueError("min_size must be less than max_size")

        if self.config.chunk_size.target_size > self.config.chunk_size.max_size:
            logger.warning("target_size is larger than max_size, adjusting target_size")
            self.config.chunk_size.target_size = self.config.chunk_size.max_size

        if self.config.chunk_size.target_size < self.config.chunk_size.min_size:
            logger.warning("target_size is smaller than min_size, adjusting target_size")
            self.config.chunk_size.target_size = self.config.chunk_size.min_size

        # 檢查閾值範圍
        if not 0.0 <= self.config.boundary.similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.config.boundary.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")

        # 檢查重疊配置
        if not 0.0 <= self.config.overlap.max_ratio <= 0.5:
            raise ValueError("overlap max_ratio must be between 0.0 and 0.5")

        # 檢查財經優化參數
        if self.config.financial.transition_penalty <= 0:
            raise ValueError("transition_penalty must be positive")

        if self.config.financial.data_continuity_bonus <= 0:
            raise ValueError("data_continuity_bonus must be positive")

        # 檢查 embedding 配置
        if self.config.embedding.provider not in ['openai', 'local']:
            raise ValueError("embedding provider must be 'openai' or 'local'")

        if self.config.embedding.provider == 'openai' and not self.config.embedding.openai_api_key:
            # 嘗試從環境變數獲取
            self.config.embedding.openai_api_key = os.getenv('OPENAI_API_KEY')
            if not self.config.embedding.openai_api_key:
                logger.warning("OpenAI API key not provided, will fallback to local model")

    def get_config(self) -> SemanticChunkingConfig:
        """獲取當前配置"""
        return self.config

    def update_config(self, updates: Dict[str, Any]):
        """動態更新配置"""
        self._update_config_from_dict(updates)
        self._validate_config()
        logger.info("Configuration updated dynamically")

    def save_config(self, file_path: str, format: str = 'yaml'):
        """保存配置到檔案"""
        config_dict = asdict(self.config)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
            raise

    def get_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            'embedding_provider': self.config.embedding.provider,
            'embedding_model': (
                self.config.embedding.openai_model
                if self.config.embedding.provider == 'openai'
                else self.config.embedding.local_model
            ),
            'chunk_size_range': f"{self.config.chunk_size.min_size}-{self.config.chunk_size.max_size}",
            'target_chunk_size': self.config.chunk_size.target_size,
            'similarity_threshold': self.config.boundary.similarity_threshold,
            'confidence_threshold': self.config.boundary.confidence_threshold,
            'overlap_sentences': self.config.overlap.sentence_overlap,
            'financial_optimization': self.config.financial.enabled,
            'log_level': self.config.log_level
        }


def create_default_config_file(file_path: str = "semantic_chunking.yaml"):
    """創建預設配置檔案"""

    default_config = {
        'embedding': {
            'provider': 'openai',
            'openai_model': 'text-embedding-3-small',
            'local_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            'batch_size': 100,
            'max_tokens': 8000,
            'rate_limit_delay': 0.1
        },
        'chunk_size': {
            'min_size': 200,
            'max_size': 800,
            'target_size': 500,
            'min_sentences': 2
        },
        'boundary': {
            'similarity_threshold': 0.75,
            'confidence_threshold': 0.6,
            'window_size': 2,
            'local_minimum_required': True
        },
        'overlap': {
            'sentence_overlap': 2,
            'max_ratio': 0.15,
            'adaptive_overlap': True
        },
        'financial': {
            'enabled': True,
            'transition_penalty': 0.8,
            'data_continuity_bonus': 1.2,
            'custom_transitions': None,
            'custom_data_indicators': None
        },
        'enable_logging': True,
        'log_level': 'INFO',
        'cache_embeddings': True
    }

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        print(f"Default configuration file created: {file_path}")

    except Exception as e:
        print(f"Failed to create default configuration file: {e}")


# 全域配置管理器實例
_global_config_manager = None

def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """獲取全域配置管理器實例"""
    global _global_config_manager

    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_path)

    return _global_config_manager

def get_config() -> SemanticChunkingConfig:
    """獲取當前配置的便捷函數"""
    return get_config_manager().get_config()


if __name__ == "__main__":
    # 創建預設配置檔案
    create_default_config_file()

    # 測試配置載入
    config_manager = ConfigManager()
    print("Configuration Summary:")
    print(json.dumps(config_manager.get_summary(), indent=2, ensure_ascii=False))
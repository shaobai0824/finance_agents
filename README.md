# finance_agents

> **專案作者**: shaobai
> **版本**: v1.0 - 多代理人理財服務
> **框架**: LangGraph + FastAPI + React

## 🎯 專案概述

基於 LangGraph 框架的多代理人理財諮詢系統，整合理財專家、金融專家、法律專家，提供專業、透明的投資建議服務。

### 核心特色
- 🧠 **智能路由管理** - 自動判斷需要哪些專家參與
- 💰 **多專家協作** - 理財/金融/法律專家共同提供建議
- 📊 **專業 RAG 查詢** - 各專家獨立的知識庫系統
- 🔐 **安全數據存取** - 銀行資料、金融數據、法律條文的安全整合
- 👥 **HITL 人工監督** - 人工審核確保建議品質

## 🚀 快速入門

**重要**: 請先閱讀 `CLAUDE.md` - 包含給 Claude Code 的關鍵開發規則

### 1. 環境設定
```bash
# 建立虛擬環境
python -m venv finance_agents_env
source finance_agents_env/bin/activate

# 安裝相依套件
pip install -r requirements.txt
```

## 📋 開發狀態

- [x] **專案初始化** - 完成結構設計
- [ ] **核心代理人系統** - LangGraph 工作流程
- [ ] **RAG 知識庫** - ChromaDB 向量搜尋
- [ ] **FastAPI 後端** - API 端點實作
- [ ] **React 前端** - 聊天介面開發
- [ ] **HITL 審核系統** - 人工監督機制

**專案作者**: shaobai | 多代理人理財服務系統 🤖💰

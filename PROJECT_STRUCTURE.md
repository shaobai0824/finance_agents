# 📁 TaskMaster & Claude Code Collective - 專案結構總覽

## 🎯 專案結構說明

本專案已根據 TaskMaster 系統架構完全重新組織，以下是當前的完整目錄結構：

```
📦 TaskMaster & Claude Code Collective
├── 📄 README.md                        # 🏠 系統總覽和快速開始
├── 📄 CLAUDE_TEMPLATE.md               # ⭐ 主初始化範本 (自動觸發 TaskMaster)
├── 📄 PROJECT_STRUCTURE.md             # 📁 本檔案：專案結構說明
├── 📄 LICENSE                          # ⚖️ 開源授權條款
├── 📄 .gitignore                       # 🚫 Git 忽略檔案配置
├── 📄 .mcp.json                        # 🔧 MCP 服務配置
├── 📁 .claude/                         # 🤖 TaskMaster 核心系統
│   ├── 🚀 taskmaster.js                # TaskMaster 核心引擎 (5個主要類別)
│   ├── 📋 GETTING_STARTED.md           # 完整初學者指南 (8步驟教學)
│   ├── 🏗️ ARCHITECTURE.md             # 系統架構設計 + 完整設計分析
│   ├── 🤖 TASKMASTER_README.md         # 技術文檔和功能說明
│   ├── 🆘 TROUBLESHOOTING.md           # 故障排除和常見問題
│   ├── 🔗 SUBAGENT_INTEGRATION_GUIDE.md # 智能體整合機制說明
│   ├── 📄 README.md                    # .claude 目錄總覽
│   ├── 📄 settings.local.json          # Claude Code 本地設定
│   ├── 📁 commands/                    # 🎛️ TaskMaster 指令系統 (8個指令)
│   │   ├── 🎯 task-init.md             # 專案初始化指令
│   │   ├── 📊 task-status.md           # 狀態查詢指令
│   │   ├── 🎪 task-next.md             # 下個任務智能建議
│   │   ├── 🤖 hub-delegate.md          # Hub 協調委派指令
│   │   ├── 🔍 review-code.md           # 程式碼審查指令
│   │   ├── 🎛️ suggest-mode.md          # 建議密度調整
│   │   ├── ✅ check-quality.md         # 品質檢查指令
│   │   └── 📝 template-check.md        # 範本檢查指令
│   ├── 📁 taskmaster-data/             # 💾 專案資料存儲 (使用時動態產生)
│   │   ├── 📄 project.json             # 專案配置檔案
│   │   └── 📄 wbs-todos.json           # WBS Todo List 狀態檔案
│   ├── 📁 agents/                      # 🤖 Claude Code 智能體配置 (7個)
│   │   ├── 🔧 general-purpose.md       # 通用任務處理智能體
│   │   ├── 🔍 code-quality-specialist.md # 程式碼品質專家
│   │   ├── 🧪 test-automation-engineer.md # 測試自動化工程師
│   │   ├── 🔒 security-infrastructure-auditor.md # 安全基礎設施稽核員
│   │   ├── 🚀 deployment-expert.md     # 部署專家
│   │   ├── 📚 documentation-specialist.md # 文檔專家
│   │   ├── ⭐ workflow-template-manager.md # 工作流程範本管理員
│   │   └── 🌐 e2e-validation-specialist.md # 端到端驗證專家
│   ├── 📁 context/                     # 📈 跨智能體上下文共享
│   │   ├── 📁 decisions/               # 技術決策記錄 (ADR)
│   │   ├── 📁 quality/                 # 程式碼品質報告
│   │   ├── 📁 testing/                 # 測試執行報告
│   │   ├── 📁 e2e/                    # 端到端測試報告
│   │   ├── 📁 security/               # 安全稽核報告
│   │   ├── 📁 deployment/             # 部署維運報告
│   │   ├── 📁 docs/                   # 文檔管理報告
│   │   └── 📁 workflow/               # 工作流程管理報告
│   └── 📁 ARCHIVE/                     # 🗃️ 舊架構檔案歸檔
│       ├── 📁 duplicated-claude-dir/   # 重複的 .claude 目錄
│       └── 📁 old-template-docs/       # 舊版範本文檔
│           ├── 📄 AI_Driven_CLI_Workflow_Setup_Guide.md
│           ├── 📄 TEMPLATE_SETUP_CHECKLIST.md
│           ├── 📄 TEMPLATE_SUMMARY.md
│           ├── 📄 TEMPLATE_USAGE_GUIDE.md
│           └── 📁 Claude Code Starter Template/
└── 📁 VibeCoding_Workflow_Templates/   # 🎨 企業級開發範本庫 (完整10個)
    ├── 📊 01_project_brief_and_prd.md        # 專案簡報與 PRD
    ├── 🧪 02_behavior_driven_development_guide.md # BDD 行為驅動開發
    ├── 🏗️ 03_architecture_and_design_document.md # 架構與設計文件
    ├── 🔧 04_api_design_specification.md      # API 設計規格
    ├── 📋 05_module_specification_and_tests.md # 模組規格與測試
    ├── 🛡️ 06_security_and_readiness_checklists.md # 安全與就緒檢查
    ├── 📁 07_project_structure_guide.md       # 專案結構指南
    ├── 📝 08_code_review_and_refactoring_guide.md # 程式碼審查與重構
    ├── 🚀 09_deployment_and_operations_guide.md # 部署與維運指南
    └── 📚 10_documentation_and_maintenance_guide.md # 文檔與維護指南
```

## 🔧 整理完成的改進

### ✅ **符合 TaskMaster 架構設計**
1. **核心檔案就位**: `taskmaster.js` 核心引擎在正確位置
2. **完整文檔體系**: 8 個層次的文檔，涵蓋所有用戶需求
3. **指令系統完整**: 8 個 TaskMaster 指令都有完整文檔
4. **VibeCoding 範本標準化**: 完整的 10 個企業級範本

### ✅ **智能體配置完整**
1. **恢復 agents 配置**: Hub-delegate 需要讀取智能體配置來進行協調
2. **恢復 context 目錄**: 智能體間協作需要上下文共享機制
3. **補充缺失配置**: 新增 `general-purpose.md` 和 `workflow-template-manager.md`
4. **歸檔冗餘檔案**: 移至 `ARCHIVE/old-template-docs/` 和 `ARCHIVE/duplicated-claude-dir/`

### ✅ **VibeCoding 範本完善**
1. **重新編號**: 按照標準 01-10 編號
2. **補充缺失**: 新增 08、09、10 範本
3. **命名標準化**: 統一檔案命名規則
4. **內容完整**: 每個範本都包含完整的指導內容

## 🎯 使用說明

### 📋 **新手用戶**
1. 閱讀 `README.md` 了解系統總覽
2. 跟隨 `.claude/GETTING_STARTED.md` 完成 8 步驟設定
3. 複製 `CLAUDE_TEMPLATE.md` 開始第一個專案

### 🔧 **進階用戶**
1. 查看 `.claude/ARCHITECTURE.md` 了解系統設計
2. 參考 `.claude/TASKMASTER_README.md` 學習技術細節
3. 使用 8 個 TaskMaster 指令進行開發協作

### 🎨 **範本使用**
1. `VibeCoding_Workflow_Templates/` 包含 10 個企業級範本
2. TaskMaster Hub 會智能匹配相關範本
3. 支援 JIT (Just-in-Time) 範本載入

## 📝 注意事項

### 💾 **動態產生的目錄**
- `.claude/taskmaster-data/` 會在專案初始化時自動建立
- 包含 `project.json` 和 `wbs-todos.json` 兩個核心檔案

### 🗃️ **ARCHIVE 目錄**
- 保留所有舊檔案供參考
- 可以安全刪除，但建議保留作為歷史記錄
- 不影響 TaskMaster 系統運作

### 🔄 **版本控制**
- 所有 TaskMaster 核心檔案都在版本控制中
- `taskmaster-data/` 目錄建議加入 `.gitignore`（如需要）
- VibeCoding 範本可以客製化和版本化

---

**🚀 TaskMaster 專案結構整理完成！準備好體驗人類主導的智能開發協作了嗎？** 🤖⚔️
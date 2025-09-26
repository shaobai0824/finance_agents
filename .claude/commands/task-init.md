---
description: TaskMaster project initialization integrated with CLAUDE_TEMPLATE.md workflow
argument-hint: [project-name] --template=[template] --mode=[mode]
allowed-tools: Read(/**), Write(/**), Edit(/**), Bash(*), Glob(*), Grep(*)
---

# 🚀 TaskMaster Project Initialization (Integrated)

## 🎯 自動觸發條件

**當偵測到 `CLAUDE_TEMPLATE.md` 檔案時，自動執行此初始化流程**

## 📋 TaskMaster 初始化流程

### Step 1: 基礎資訊收集（繼承 CLAUDE_TEMPLATE.md）
```
✅ 從 CLAUDE_TEMPLATE.md 工作流程繼承：
├── PROJECT_NAME: $1
├── PROJECT_DESCRIPTION: [已收集]
├── 主要程式語言: [已確認]
├── VibeCoding 7問澄清: [已完成]
└── 人類確認設定: [已確認]
```

### Step 2: TaskMaster 智能分析（文檔導向流程）

```
🤖 TaskMaster Hub 分析進行中...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 載入相關 VibeCoding 範本...
📄 生成文檔導向任務流程 (Phase 1-2 文檔 → 駕駛員審查 → Phase 3 開發)...
🤖 Hub-and-Spoke 協調策略分析...
📊 專案複雜度和文檔需求評估...
📋 建立包含審查閘道的 WBS Todo List 結構...
🔍 設置駕駛員審查檢查點...
```

### Step 3: TaskMaster 專案計劃展示

```
📊 TaskMaster 專案初始化計劃:
══════════════════════════════════════════════════════════

🎯 專案名稱: $1
📝 專案描述: [從 CLAUDE_TEMPLATE 繼承]
🏗️ 專案類型: [基於 7問分析判定]

📚 載入的 VibeCoding 範本:
├── 06_project_structure_guide.md (相關度: 95%)
├── 03_architecture_and_design_document.md (相關度: 88%)
├── 04_module_specification_and_tests.md (相關度: 82%)
├── 05_security_and_readiness_checklists.md (相關度: 75%)
└── [其他相關範本...]

📝 生成的文檔導向任務列表: [計算中...]
📄 Phase 1-2 文檔生成計劃: [規劃中...]
🤖 Hub 協調策略: [分析中...]
⏱️ 文檔審查及開發時程: [評估中...]
```

### Step 4: Hub-and-Spoke 分析結果

```
🎯 TaskMaster Hub 協調分析:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 專案複雜度: [Low/Medium/High]
🎯 協調策略: [Sequential/Parallel/Hybrid]
📈 預估成功率: [Based on analysis]

🤖 建議的智能體協調順序:
1. 🏗️ infrastructure-agent → 專案基礎設置
2. 🟡 code-quality-specialist → 品質框架建立
3. 🔴 security-infrastructure-auditor → 安全基線檢查
4. 🟢 test-automation-engineer → 測試框架建置
5. 📝 documentation-specialist → 文檔體系建立

📋 WBS Todo List 預覽:
├── Phase 1: 專案設置 (5 tasks, ~2 hours)
├── Phase 2: 開發環境 (8 tasks, ~3 hours)
├── Phase 3: 核心功能 (12 tasks, ~8 hours)
└── Phase 4: 品質保證 (6 tasks, ~2 hours)

總計: 31 tasks, 預估 15 hours
```

### Step 5: 人類駕駛員最終確認

```
🤖⚔️ 人類駕駛員決策點:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ TaskMaster 專案初始化確認:

🎯 專案設定確認:
  [1] ✅ 確認 TaskMaster 計劃，開始初始化
  [2] 🔧 調整任務優先順序和範圍
  [3] 📋 查看完整任務列表詳情
  [4] 🤖 修改 Hub 協調策略
  [5] 📚 調整 VibeCoding 範本選擇
  [6] ❌ 取消 TaskMaster 初始化

🎛️ TaskMaster 模式選擇:
  [H] HIGH - 每個任務都需要人類確認
  [M] MEDIUM - 關鍵決策點確認 (推薦)
  [L] LOW - 僅重要里程碑確認
  [A] ADVISORY - Hub 建議模式，最小干預

🛡️ 緊急控制設定:
  [P] 設置暫停檢查點
  [S] 啟用即時狀態監控
  [E] 配置緊急停止機制

請選擇專案設定 (1-6) 和模式 (H/M/L/A):
```

### Step 6: TaskMaster 系統建立

**如果確認初始化，TaskMaster 將執行：**

```
🚀 TaskMaster 系統建立中...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 建立專案目錄結構
✅ 初始化 .claude/taskmaster-data/
   ├── project.json (專案配置)
   └── wbs-todos.json (WBS Todo List)
✅ 載入 TaskMaster 核心系統
✅ 配置 Hub-and-Spoke 協調器
✅ 建立 VibeCoding 範本整合
✅ 生成客製化 CLAUDE.md
✅ 設定 Git 和專案檔案
✅ 刪除 CLAUDE_TEMPLATE.md

🎉 TaskMaster 專案初始化完成！
```

### Step 7: 立即可用功能

```
📋 TaskMaster 控制中心已啟用:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎛️ 立即可用命令:
├── /task-status     → 查看完整專案狀態
├── /task-next       → 獲得下個智能任務建議
├── /hub-delegate    → Hub 協調智能體委派
├── /suggest-mode    → 調整 TaskMaster 模式
└── /review-code     → Hub 協調程式碼審查

📊 WBS Todo List 已建立:
├── 📋 總任務: 31 個
├── ⏳ 待處理: 31 個
├── 🎯 當前: 準備開始第一個任務
└── 📈 進度: 0% (初始化完成)

💡 建議下一步:
1. 使用 /task-next 開始第一個任務
2. 使用 /task-status 查看詳細狀態
3. 隨時可用 /pause 暫停 TaskMaster
```

## 🔧 進階初始化選項

### 範本特化初始化
```bash
/task-init my-project --template=react-typescript
/task-init my-project --template=api-service
/task-init my-project --template=ai-ml-project
```

### 協調模式設定
```bash
/task-init my-project --mode=sequential    # 序列執行，每步確認
/task-init my-project --mode=parallel      # 並行優化執行
/task-init my-project --mode=advisory      # 建議模式，最小干預
```

## 🤖⚔️ 與 CLAUDE_TEMPLATE.md 的整合優勢

### 1. 無縫承接
- 自動繼承 CLAUDE_TEMPLATE.md 的所有設定
- VibeCoding 7問分析直接轉為任務生成依據
- Linus 心法整合到 Hub 協調邏輯

### 2. 智能增強
- 基於需求分析自動選擇相關 VibeCoding 範本
- Hub 智能分析專案複雜度和協調策略
- WBS Todo List 提供全局開發狀態掌控

### 3. 人類控制
- 保持 CLAUDE_TEMPLATE.md 的人類主導理念
- 所有 TaskMaster 決策都需要人類確認
- 緊急控制機制隨時可用

**Ready to initialize your TaskMaster-powered project!** 🚀🤖⚔️
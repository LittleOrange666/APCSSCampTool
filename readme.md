# APCSS x APCS Guide Camp Tool (導航營工具組)

此專案為 **APCSS x APCS 導航營** 設計的輔助工具組，結合了 **Discord 機器人** 與 **FastAPI 網頁服務**。它能從指定的 QingdaoUOJ 獲取學生提交狀態、計算基礎與進階題目進度，並提供遠端程式執行（Code Runner）、Discord 頻道發言統計等豐富功能。

---

## 🌟 功能特色

### 1. Discord 機器人功能 (`modules/dc.py`)
機器人提供多個斜線指令（Slash Commands），方便助教與學生直接於 Discord 互動：
*   **`/查詢證書`**: 查詢指定使用者的基礎與進階證書達成進度，並能自動對照學號與真實姓名。
*   **`/進度分析`**: 詳細分析使用者在各個題目分類（如：變數/輸入輸出、條件判斷/迴圈、動態規劃等）的得分率。
*   **`/組別排行`**: 顯示「基礎班」或「進階班」目前得分前幾名的排行榜。
*   **`/訊息排名`**: 統計特定頻道內使用者的歷史發言次數，並具備自動分批讀取與快取機制以防觸發 rate limit。
*   **`/執行程式`**: 提供簡易沙盒執行環境，支援 C++17、Python 3 與 Java 8 程式碼的線上運行（依賴 OrangeJudge API）。
*   **`/破冰`**: 趣味破冰指令，回覆 `Ciallo～(∠・ω< )⌒★`。

### 2. 證書查詢網頁 (`templates/query.html`)
*   提供一個簡潔易用的前端網頁，使用者可在網頁輸入 OJ 帳號，快速查詢基礎班（標準：9600分）及進階班（標準：7900分）的結業證書取得狀態。
*   提供後端 API `/query` (POST) 供前端查詢分數及上次更新時間。

### 3. 排行榜凍結機制 (`modules/tool.py`)
*   支援透過環境變數 `OJ_FREEZE_TIME` 設定排行榜凍結時間。凍結後，系統將停止向 OJ API 請求最新數據，改為讀取本地快取 (`cache.json`)，以配合營隊競賽結算需求。

---

## 📂 專案架構

```text
├── main.py                # 程式進入點，同時啟動 Discord 機器人與 FastAPI 網頁伺服器
├── requirements.txt       # Python 套件依賴清單
├── Dockerfile             # 用於建置 Python 執行環境的 Docker 映像檔
├── docker-compose.yml     # 定義服務容器（Web+Bot、Cloudflared 隧道）
├── run.sh                 # 本地快速建置並啟動 Docker Compose 的指令檔
├── build_release.sh       # 用於推送 Release 映像檔至 Docker Hub 的指令檔
├── qindaou_info.json      # 快取 OJ 連線設定與登入 cookie 的暫存檔
├── cache.json             # 儲存 OJ 成績與分數的本地快取檔
├── templates/
│   └── query.html         # 證書查詢的前端網頁範本
├── data/
│   ├── names.csv          # 學員帳號對照表（格式：OJ帳號,真實姓名）
│   └── count_cache.json   # 訊息量統計指令的快取檔案
└── modules/
    ├── __init__.py
    ├── dc.py              # Discord 機器人主程式與 Slash 指令註冊
    ├── tool.py            # 成績抓取、計算、凍結邏輯與快取管理
    ├── qindaou.py         # 封裝對 QingdaoUOJ API 的連線與登入驗證
    └── submit.py          # 呼叫 OrangeJudge API 進行遠端代碼編譯執行
```

---

## ⚙️ 環境變數配置

請在專案根目錄建立 `.env` 檔案，並填入以下設定：

```ini
# Discord 設定
DISCORD_BOT_TOKEN=your_discord_bot_token_here
ALLOWED_CHANNEL_IDS=1392374490553516052,1267373672126218243 # 限制僅能在這些 Discord 頻道執行指令（逗號分隔）

# QingdaoUOJ 平台設定
QingdaoUOJ_URL=https://apcs-simulation.com
QingdaoUOJ_ACCOUNT=admin_username
QingdaoUOJ_PASSWORD=admin_password
OJ_CONTEST_ID=29                                           # 營隊對應的 Contest ID

# OrangeJudge 程式代碼執行環境設定 (Code Runner)
ORANGEJUDGE_URL=https://your-orangejudge-url
ORANGEJUDGE_USERNAME=runner_username
ORANGEJUDGE_API_KEY=runner_api_key

# 系統控制參數
OUTPUT_LIMIT=10                                            # 排行榜或訊息排名顯示的最大數量
# OJ_FREEZE_TIME=2025-07-20T12:00:00                       # 選填，設定封榜時間（ISO 8601 格式），若啟用則只讀取快取
# OJ_CACHE_FILE=cache.json                                 # 選填，快取檔路徑

# Cloudflare Tunnel 連接設定
CLOUDFLARED_TUNNEL_TOKEN=your_cloudflared_tunnel_token     # Cloudflared 穿透憑證
```

---

## 🚀 部署與執行

本專案支援 Docker 容器化部署，並結合了 Cloudflared 隧道，讓外部能安全地存取本機開發伺服器。

### 方式 A：使用 Docker 部署（推薦）

1. 確保已安裝 Docker 與 Docker Compose。
2. 配置好 `.env` 檔案。
3. 執行啟動腳本：
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   此腳本會自動建置 `apcs_tool:latest` 映像檔，並以後台模式啟動服務。

### 方式 B：手動在本地執行

1. 安裝所需依賴：
   ```bash
   pip install -r requirements.txt
   ```
2. 設定環境變數（或將其寫入系統變數中）。
3. 啟動服務：
   ```bash
   python main.py
   ```
   伺服器將在 `http://localhost:8070` 啟動，而 Discord 機器人亦會同步上線。

---

## 📊 分類對照表

專案內定義的題目分類代碼與對應的中文標籤如下（`modules/tool.py`）：

| 代碼 | 分類名稱 | 難易度歸類 |
|:---:|:---|:---:|
| **A** | 變數/輸入輸出 | 基礎班 (Easy) |
| **B** | 條件判斷/迴圈 | 基礎班 (Easy) |
| **C** | 陣列/字串 | 基礎班 (Easy) |
| **D** | 函式/遞迴 | 基礎班 (Easy) |
| **E** | 結構 | 基礎班 (Easy) |
| **G** | 資料結構 | 基礎班 (Easy) |
| **H** | 運算思維實作實務解析 (基礎) | 基礎班 (Easy) |
| **L** | 實作與除錯技巧 | 基礎班 (Easy) |
| **Z01-Z03** | 運算思維實作挑戰賽基礎題 | 基礎班 (Easy) |
| **F** | 時間複雜度 | 進階班 (Hard) |
| **I** | 枚舉/二分搜 | 進階班 (Hard) |
| **J** | 貪心 | 進階班 (Hard) |
| **K** | 圖論 | 進階班 (Hard) |
| **M** | 動態規劃 | 進階班 (Hard) |
| **N** | 運算思維實作實務解析 (進階) | 進階班 (Hard) |
| **Z04-Z06** | 運算思維實作挑戰賽進階題 | 進階班 (Hard) |
| **Z** | 運算思維實作挑戰賽 | 其他 |

---

## 📝 備註與開發

*   **帳號對照**: 請將學員的 OJ 帳號與真實姓名對照表放入 `data/names.csv` 中，格式為 `OJ帳號,姓名`（例如 `awp2601,張三`），否則 `/查詢證書` 會發出非標準帳號警告。
*   **Release 發布**: 可以執行 `./build_release.sh <版本號>` 來打包並推送映像檔（例如 `./build_release.sh 1.2.0`）。
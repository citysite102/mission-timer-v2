# CLAUDE.md

## 專案概要
單檔專注計時器，部署在 GitHub Pages。所有 HTML／CSS／JS 都在 `mission-timer/index.html`，沒有框架、建置步驟、套件或測試。
根目錄的 `index.html` 只用 meta refresh 導到 `mission-timer/`，好讓 Pages 網址直接開啟計時器，不要在裡面加內容。

## 本機執行
```bash
python3 -m http.server 8000 --directory mission-timer
```
（`.claude/launch.json` 已設定好 `mission-timer` 預覽，使用 port 8765。）

## 原則
- 維持單檔、零依賴：不引入框架、CDN。唯一的外部請求是 Open-Meteo（日出／日落，免金鑰、逾時 8 秒，失敗時顯示「離線」）。
- UI 文字、註解、commit 訊息都用繁體中文。
- 功能有變動時，要同步更新 README.md 的「功能」段落。

## 設計規範
- 深色星空背景。橘色主色只用在當下要強調的那一個主要動作（如「發射」、彈窗的「確認」）；青色霓虹是輔助色，不受此限。
- 主要按鈕使用航太語彙：發射（開始）、待機（暫停）、返航（重設）、補給（時長設定）、停泊（5 分鐘休息，不計趟數）。彈窗裡的「取消／確認」等通用操作維持原樣。
- 倒數相關的分鐘數（`DEFAULT_MIN`、`PRESETS`、`MAX_MIN`、`DOCK_MIN`）集中放在 `<script>` 最上方的設定區，不要在 HTML 或其他程式碼裡寫死。

## 程式結構（index.html 的 `<script>` 由上而下）
1. 計時器：用 `endAt`（目標時刻）推算剩餘時間，不是逐 tick 遞減，所以背景分頁不會累積誤差。`render()` 約每 31ms 跑一次，負責更新數字、分頁標題、進度條和火箭位置。
2. 時長設定：使用 `<dialog>` + `form method="dialog"`，範圍 1 秒到 `MAX`（180:59）；飛行中會停用 `#openSet`。
3. 3D 火箭：在 `#rocket` canvas 上手刻多邊形渲染（旋轉體 `PROF` 加四片尾翼，依深度排序）。
4. 人造衛星：IIFE 產生等角投影的 SVG 字串，寫入 `#sat`。
5. 背景星球：粒子點陣，透過 `dot()` 依「色階 × 透明度」分桶進 `Path2D`，再由 `flush()` 一次填滿。新增繪製時要沿用這組函式，不要每個點各自設定 `fillStyle`。
   - 行星定義在 `PLANETS`（glow、haze、disk、colors、tone，木星另有 ring）。新增行星時，要在 `PLANETS` 和 `nav.planets` 各補一筆。
   - `resize()` 只產生可能入鏡的緯度帶；`tones` 快取會在 resize 時清空。
   - 星星座標寫死在 `STARS`，光環用固定種子產生，不要改成每次隨機。
   - 主迴圈節流在約 30fps。

## 必須保留的行為
- `prefers-reduced-motion`：`still` 為 true 時只畫靜態一幀（`draw(0)`），CSS 也會關掉所有 animation。新加的動畫都要遵守這點。
- 今日任務數：只有倒數自然跑到 0 才 +1（返航不算），以本機時間午夜歸零；存在 localStorage `mt-today`，刻意不跨裝置同步。
- localStorage 鍵為 `mt-duration`、`mt-planet`、`mt-today`，讀寫一律包在 try/catch 裡。
- 進度條、火箭、背景 canvas 都設了 aria-hidden；`#status` 是 aria-live。

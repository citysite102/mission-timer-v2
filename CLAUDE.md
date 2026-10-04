# CLAUDE.md

## 專案概要
單檔專注計時器，部署在 GitHub Pages。所有 HTML／CSS／JS 都在 `mission-timer/index.html`，沒有框架、建置步驟、套件或測試。

- **根目錄 `index.html` 只能放導向 `mission-timer/` 的內容。**
  原因：GitHub Pages 網址會先開這個檔，它只負責把人帶到計時器。
  例：`<meta http-equiv="refresh" content="0; url=mission-timer/">`
  例外：可以有 `<title>`，以及給停用自動轉址的人點的 `<a href="mission-timer/">` 備用連結。

## 本機執行
```bash
python3 -m http.server 8000 --directory mission-timer
```
（`.claude/launch.json` 已設定好 `mission-timer` 預覽，使用 port 8765。）

## 原則
- **計時器的 HTML、CSS、JS 只能寫在 `mission-timer/index.html`。**
  原因：沒有建置步驟，Pages 直接提供這個檔案。
  例：新增樣式寫進檔內的 `<style>`，不要另開 `style.css`。
- **程式碼只能用瀏覽器原生 API。**
  原因：零依賴，離線也能開，不會因為 CDN 掛掉而壞掉。
  例：日期格式化用 `toLocaleDateString`，不要裝 dayjs。
- **執行期唯一的外部請求是 Open-Meteo。**
  原因：日出／日落需要即時資料，其他功能都能在本機算出來。
  例：`fetch('https://api.open-meteo.com/…')`
- **Open-Meteo 請求要設 8 秒逾時，失敗時顯示「離線」。**
  原因：網路不好時，畫面不能卡在讀取中。
  例：`AbortSignal.timeout(8000)`；在 catch 裡把 `#sun` 改成「離線」。
- **UI 文字、註解、commit 訊息只能用繁體中文。**
  例：狀態文字寫「停泊結束」，不寫 "Docked"。
  例外：程式識別字（`endAt`）、技術名詞（canvas、localStorage）、commit 結尾的 `Co-Authored-By` 署名行。
- **使用者看得到的行為一改變，同一個 commit 裡就要更新 README.md 的「功能」段落；新增或改名按鈕時，也要更新按鈕表。**
  原因：README 是使用者唯一的說明文件。
  例：新增停泊時，同時補了按鈕表的一列和「功能」的一條。
  例外：不影響行為的重構、效能調整、純 bug 修正，不用更新。

## 設計規範
- **背景只能是深色星空，也就是 `#bg` canvas 畫的星星和星球。**
  原因：這是整個介面的主題。
  例：新增區塊用半透明深色底，讓星空透出來。
- **同一個畫面狀態下，最多只能有一個按鈕帶 `.primary`（橘色）。**
  原因：讓使用者一眼就知道下一步該按哪裡。
  例：主畫面是「發射」；彈窗打開時是「確認」。
- **其他需要強調的元素用青色霓虹，數量不限。**
  原因：輔助色負責層次，不搶主要動作。
  例：「停泊」用預設的青色光效。
- **主畫面上的操作按鈕只能用航太語彙命名，而且不能和現有的名稱重複。**
  原因：維持太空任務的主題；名稱重複會讓人分不清。
  例：發射＝開始、待機＝暫停、返航＝重設、補給＝時長設定、停泊＝5 分鐘休息。
  例外：彈窗裡的「取消」「確認」等通用操作照常用一般說法。
- **倒數相關的分鐘數只能在 `<script>` 最上方的「設定」區定義成常數（`DEFAULT_MIN`、`PRESETS`、`MAX_MIN`、`DOCK_MIN`），其他地方一律引用常數。**
  原因：要調整時長只需改一個地方。
  例：寫 `DOCK_MIN * 60 * 1000`，不要寫 `300000`。
  例外：從常數推導出來的值（例如由 `MAX_MIN` 算出的 `MAX`），以及單位換算用的 `60`、`1000`。

## 程式結構（index.html 的 `<script>` 由上而下）
1. 計時器：用 `endAt`（目標時刻）推算剩餘時間。`render()` 約每 31ms 跑一次，負責更新數字、分頁標題、進度條和火箭位置。
2. 時長設定：使用 `<dialog>` + `form method="dialog"`，範圍 1 秒到 `MAX`（180:59）；飛行中會停用 `#openSet`。
3. 3D 火箭：在 `#rocket` canvas 上手刻多邊形渲染（旋轉體 `PROF` 加四片尾翼，依深度排序）。
4. 人造衛星：IIFE 產生等角投影的 SVG 字串，寫入 `#sat`。
5. 背景星球：粒子點陣，透過 `dot()` 依「色階 × 透明度」分桶進 `Path2D`，再由 `flush()` 一次填滿。
   - 行星定義在 `PLANETS`（glow、haze、disk、colors、tone，木星另有 ring）。
   - `resize()` 只產生可能入鏡的緯度帶；`tones` 快取會在 resize 時清空。
   - 主迴圈節流在約 30fps。

### 修改這些區塊時的規則
- **背景 canvas 上新增的粒子只能用 `dot()` 加入，最後由 `flush()` 一次畫出。**
  原因：粒子有上萬顆，每顆各自切換 `fillStyle` 會拖慢畫面。
  例：新增光環的點用 `dot(x, y, r, tone, alpha)`。
  例外：不是粒子的單一圖形（例如大氣輝光的漸層），可以直接用 `ctx` 畫。
- **新增行星時，`PLANETS` 和 HTML 的 `<nav class="planets">` 都要各補一筆，而且 key 要一致。**
  原因：缺一邊會選不到，或按了沒反應。
  例：`PLANETS.saturn` 對應 `<button data-p="saturn">`。
- **星星只能來自寫死的 `STARS` 陣列。**
  原因：每次重繪位置都一樣，畫面才不會閃。
  例：要加星星就在 `STARS` 補 `[x, y, r, a]`。
- **光環只能用固定種子的 `rnd()` 產生。**
  原因：每次重繪位置都一樣，畫面才不會閃。
  例：`let seed = 7`

## 必須保留的行為
- **剩餘時間只能用 `endAt - Date.now()` 算出來。**
  原因：瀏覽器會降低背景分頁的計時器頻率，逐 tick 遞減會越跑越慢。
  例：`render()` 裡的 `Math.max(0, endAt - Date.now())`。
  例外：暫停時直接顯示 `remaining`。
- **JS 動畫只能在 `still`（`prefers-reduced-motion`）為 false 時啟動。**
  原因：有些使用者看到動態效果會不舒服。
  例：`still ? draw(0) : requestAnimationFrame(loop)`
- **CSS 動畫只能用 `animation` 屬性，這樣既有的 `animation: none !important` 才關得掉。**
  原因：有些使用者看到動態效果會不舒服。
  例：新動畫寫 `animation: pulse 2s infinite`。
  例外：滑鼠移上去的 `transition` 不受此限。
- **只有任務倒數自然跑到 0，今日趟數才 +1。**
  原因：趟數代表真正完成的專注時段。
  例：`render()` 裡的 `countDone(1)`。
  例外：返航和停泊跑完都不算。
- **今日趟數在本機時間午夜歸零。**
  原因：「今天」以使用者所在的時區為準。
  例：`toLocaleDateString('sv')`
- **今日趟數只能存在這台裝置的 localStorage `mt-today`。**
  原因：刻意不跨裝置同步，所以不需要帳號和後端。
- **localStorage 的鍵只能用 `mt-` 開頭，新增的鍵要補進這份清單：`mt-duration`、`mt-planet`、`mt-today`。**
  原因：避免和同網域的其他頁面衝突。
- **每一次 localStorage 讀寫都要包在 try/catch 裡。**
  原因：無痕模式或封鎖網站資料時，存取會丟出例外，導致整頁壞掉。
  例：`try { localStorage.setItem(…) } catch {}`
- **純裝飾的視覺元素都要設 `aria-hidden="true"`。**
  原因：螢幕報讀器不需要唸出裝飾。
  例：`#bg`、`.track`（內含火箭）、`.sat`。
- **狀態變化只能透過 `#status` 播報。**
  原因：它是 `aria-live`，報讀器只會唸這裡。
  例：停泊結束時把 `#status` 改成「停泊結束」。

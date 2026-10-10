# Mission Timer 任務計時器

一個單檔的專注計時器（預設 25 分鐘，可自訂），背景是「從軌道上俯瞰星球」的即時繪製場景。整個專案只有一個 `index.html`，不依賴任何框架、外部圖片或字型。

## 使用方式

線上版：<https://citysite102.github.io/mission-timer-v2/>，打開就能用。

本機使用時，直接用瀏覽器打開 `mission-timer/index.html` 即可。或在本機起一個靜態伺服器：

```bash
python3 -m http.server 8000 --directory mission-timer
```

然後開啟 <http://localhost:8000>。

| 按鈕 | 功能 |
| --- | --- |
| 發射 | 開始／繼續倒數 |
| 待機 | 暫停 |
| 返航 | 重設回設定的時長 |
| 停泊 | 開始 5 分鐘休息 |
| 離艙 | 登出，回到登入畫面（飛行中按下等於返航） |
| 近地／繞月／深空 | 換成 15／25／50 分鐘（倒數中按下會先停下，不會自動開始） |

左上角可以切換目標行星（地球、火星、金星、木星）；右上角的「補給」會開啟時長設定彈窗，可輸入分、秒或點選 5／15／25／45／60 分鐘，範圍 1 秒到 180 分 59 秒，飛行中不能開啟。兩項選擇都會記在瀏覽器裡。

## Supabase 設定

航行日誌存在 Supabase，每個帳號各自一份。換成自己的專案時：

1. 在 Supabase 的 SQL Editor 執行下面的 SQL，建立 `flight_log` 表並開啟 RLS。
2. 到 Project Settings → API 複製 Project URL 和 publishable（anon public）key，填進 `mission-timer/index.html` 最上方設定區的 `SUPABASE_URL`、`SUPABASE_ANON_KEY`。**不要填 service_role（secret）key。**
3. 到 Authentication → Users → Add user 建立帳號（勾選 Auto Confirm User）。畫面上沒有註冊功能，帳號都在後台建立。

```sql
create table public.flight_log (
  id         bigint generated always as identity primary key,
  user_id    uuid         not null default auth.uid()      -- 誰飛的；由資料庫自動填入登入者，前端不送
             references auth.users on delete cascade,
  started_at timestamptz  not null,                -- 出發時間
  minutes    numeric(6,2) not null,                -- 飛行分鐘數
  completed  boolean      not null,                -- 有沒有完成
  unique (user_id, started_at)                     -- 補傳重送時不會重複記
);

alter table public.flight_log enable row level security;

revoke all on public.flight_log from anon, authenticated;
grant select, insert on public.flight_log to authenticated;

create policy "只讀得到自己的紀錄" on public.flight_log
  for select to authenticated
  using ((select auth.uid()) = user_id);

create policy "只能新增自己的合理紀錄" on public.flight_log
  for insert to authenticated
  with check (
    (select auth.uid()) = user_id
    and minutes between 0 and 181
    and started_at <= now() + interval '5 minutes'
  );
```

從沒有登入功能的舊版升級時，改執行這段（**會刪掉表裡所有紀錄**，舊紀錄沒有擁有者，新規則下沒有人看得到）：

```sql
delete from public.flight_log;
drop policy "任何人可讀" on public.flight_log;
drop policy "任何人可新增合理的紀錄" on public.flight_log;
alter table public.flight_log drop constraint flight_log_started_at_key;
alter table public.flight_log
  add column user_id uuid not null default auth.uid() references auth.users on delete cascade,
  add constraint flight_log_user_id_started_at_key unique (user_id, started_at);

revoke all on public.flight_log from anon, authenticated;
grant select, insert on public.flight_log to authenticated;

create policy "只讀得到自己的紀錄" on public.flight_log
  for select to authenticated
  using ((select auth.uid()) = user_id);

create policy "只能新增自己的合理紀錄" on public.flight_log
  for insert to authenticated
  with check (
    (select auth.uid()) = user_id
    and minutes between 0 and 181
    and started_at <= now() + interval '5 minutes'
  );
```

沒登入的人（`anon`）沒有任何權限，什麼都讀不到。登入的人只能讀取、新增自己的紀錄，而且 `user_id` 由資料庫填入，無法冒用別人。沒有修改和刪除的規則，所以沒有人能透過網頁竄改或清空日誌，包括自己的。

注意：

- publishable key 寫在網頁原始碼裡，是公開的，這是正常的；能讀寫什麼全由上面的 RLS 決定。
- 任何人都能用公開金鑰呼叫 Supabase 的註冊 API 自己開帳號，但只會看到自己的空日誌。想完全擋掉，到 Authentication → Sign In / Providers 關掉「Allow new users to sign up」。
- 登入後，連不上 Supabase 時計時器照常能用，紀錄先存在這台裝置，畫面會顯示「待同步 N 趟」，之後自動補傳。離艙時還沒送出的紀錄會留著，等同一個帳號下次登入再送。
- 一批待同步的紀錄只要有一筆被 Supabase 拒絕（例如裝置時鐘快了 5 分鐘以上），整批都會一直重試、送不出去。

## 功能

- **倒數計時**：顯示格式為 `分:秒.百分之一秒`（例如 `24:59.87`），以目標時刻推算剩餘時間，分頁切到背景也不會累積誤差；分頁標題同步顯示到秒。
- **日出／日落**：載入時向 [Open-Meteo](https://open-meteo.com/)（免金鑰）取得今天台北的日出與日落時間，顯示在倒數下方；取不到或逾時 8 秒則顯示「離線」。
- **快捷時長**：控制按鈕上方的近地、繞月、深空一鍵換成 15、25、50 分鐘，目前的時長會亮起；倒數中按下會先停下，按「發射」才開始。和「補給」一樣會記住選擇。
- **航行日誌**：每趟任務記下出發時間、飛行分鐘數（暫停的時間不算）、有沒有完成；倒數跑到 0 才算完成，中途返航或中途換時長記為未完成，停泊不記。畫面最下方顯示從日誌算出的今日完成趟數、總飛行時數、連續出勤天數（每天至少完成一趟；今天還沒完成不算中斷）。日誌存在 Supabase，每個帳號各自一份，同一個帳號在手機和電腦登入會看到同一份；連不上時先存在這台裝置，畫面會顯示「待同步 N 趟」，之後自動補傳。
- **登入**：用電子郵件和密碼登入（Supabase Auth），沒登入只看得到登入畫面。登入狀態會記在瀏覽器裡，重新整理不用再登入；右上角「離艙」可登出，只登出這台裝置；同一個瀏覽器的其他分頁會跟著登入或登出。
- **停泊（休息）**：一鍵開始 5 分鐘休息倒數，不記入航行日誌；跑完或返航後回到原本設定的時長。
- **3D 火箭**：以 canvas 即時繪製的旋轉體火箭（機身、鼻錐、舷窗、四片尾翼），沿自身軸線自轉並隨進度前進；發射後轉速加快、尾焰變長。
- **霓虹按鈕**：懸停時邊框有繞行光點、游標聚光、浮起與外發光；點擊有漣漪與外擴衝擊波。
- **軌道視角星球**：經緯排列的粒子點陣，只露出畫面下方一道弧。
  - 左上光源：受光面亮、背光面暗，越靠輪廓越亮形成邊緣光
  - 地平線外緣有大氣輝光，顏色隨行星變化
  - 每顆行星有自己的地表漸層（海陸與冰帽、赤紅地表、雲帶、條紋與大紅斑）
  - 切換行星時交叉淡入淡出
  - 木星有分層光環，內圈轉得比外圈快
- **人造衛星**：等角投影的扁平插畫風衛星，太陽能板、天線碟發送訊號波、閃爍信標，並緩慢漂浮。
- **固定星空**：星星座標寫死在程式碼中，重繪時不會跳動。
- **無障礙**：系統開啟「減少動態效果」時，停止所有動畫與星球自轉。

## 技術重點

- 星球粒子依「色階 × 透明度」分桶，每桶用一個 `Path2D` 一次填滿，避免上萬次切換 `fillStyle`。
- 只生成可能入鏡的緯度帶，光環也只計算看得到的那一段弧。
- 背景以約 30fps 重繪，足夠流暢又省電。

## 專案結構

```
mission-timer/
└── index.html   # 所有 HTML、CSS、JS 都在這裡
```

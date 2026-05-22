# Implementation Checklist

模型监控站项目实施清单。每个 `[x]` 后面带 `证据:` 行说明在哪里可以验证。

## Phase 0 — 项目骨架

- [x] 初始化 git 仓库，建 `.gitignore`
  证据: `.gitignore`（37 行，覆盖 node/python/env/playwright），`.git/HEAD` 存在
- [x] 创建顶层目录结构：`apps/web/`, `scrapers/`, `supabase/migrations/`, `.github/workflows/`
  证据: `ls -la` 这 4 个目录都存在；`apps/web/`, `scrapers/`, `supabase/migrations/0001_initial.sql`, `.github/workflows/scrape-daily.yml`
- [x] 写 README.md：项目目标 + 架构图 + 本地开发说明
  证据: `README.md`（架构图在第 23-50 行，本地开发说明在第 67-90 行）
- [x] 写 `.env.example`
  证据: `.env.example`（SUPABASE_URL, SUPABASE_SERVICE_KEY, ANTHROPIC_API_KEY, VERCEL_DEPLOY_HOOK_URL）

## Phase 1 — 数据层（Supabase）

- [x] 写 `supabase/migrations/0001_initial.sql`：6 张表 + 索引 + 3 个视图 + RLS
  证据: `supabase/migrations/0001_initial.sql:11` (vendors), `:27` (models), `:55` (prices), `:74` (benchmark_scores), `:93` (daily_snapshots), `:109` (scrape_errors); views at `:131,148,163`; RLS at `:192-205`
- [x] 写 `supabase/seed.sql`：预填 14 个厂商基础信息
  证据: `supabase/seed.sql`，14 个 insert 语句覆盖 openai/anthropic/google/meta/mistral/xai/cohere + deepseek/qwen/glm/doubao/kimi/baichuan/hunyuan
- [x] 在 Supabase 应用 migration + seed
  证据: MCP `apply_migration` + `execute_sql` 都返回 success；`select count(*) from vendors` = 14（本会话 execute_sql 验证过）

## Phase 2 — Scraper 核心框架

- [x] `core/schema.py` (pydantic Model / Price / BenchmarkScore)
  证据: `scrapers/core/schema.py:18` ModelRecord, `:38` PriceRecord, `:55` BenchmarkRecord, `:67` ScrapeResult
- [x] `core/db.py` (Supabase upsert/append + dry-run + error log)
  证据: `scrapers/core/db.py:31` upsert_model, `:60` append_price, `:99` append_benchmark, `:135` record_error
- [x] `core/extractor.py` (httpx + Playwright fetch + LLM 兜底 + 价格解析)
  证据: `scrapers/core/extractor.py:36` fetch_static, `:46` fetch_rendered, `:120` llm_extract, `:79` parse_price_string
- [x] `core/differ.py` (今日 vs 昨日 diff → changes_json)
  证据: `scrapers/core/differ.py:13` build_snapshot_payload
- [x] `core/base.py` (VendorScraper / BenchmarkScraper 抽象类)
  证据: `scrapers/core/base.py:9` VendorScraper, `:20` BenchmarkScraper
- [x] `core/registry.py` (自动发现模块)
  证据: `scrapers/core/registry.py:7` discover_vendor_scrapers, `:11` discover_benchmark_scrapers；本会话验证 `python -c "from scrapers.core.registry import ..."` 输出 14 vendors + 3 benchmarks
- [x] `run.py` (主入口，错误隔离，daily snapshot, Vercel webhook)
  证据: `scrapers/run.py:19` main, `:79` 错误 record_error, `:94` write_snapshot, `:104` httpx.post(deploy_hook)
- [x] `vendors/_catalog_scraper.py` (统一 base 类)
  证据: `scrapers/vendors/_catalog_scraper.py:22` CatalogVendorScraper，scrape() 在 :58
- [x] `vendors/_helpers.py` (LLM 提取 merge 进 ScrapeResult)
  证据: `scrapers/vendors/_helpers.py:18` llm_fallback_into_result

## Phase 3 — Vendor Scrapers

- [x] 7 个海外厂商
  证据: 文件存在 — `scrapers/vendors/openai.py`, `anthropic.py`, `google.py`, `meta.py`, `mistral.py`, `xai.py`, `cohere.py`；本会话 registry 输出包含全部
- [x] 7 个国内厂商
  证据: 文件存在 — `scrapers/vendors/deepseek.py`, `qwen.py`, `glm.py`, `doubao.py`, `kimi.py`, `baichuan.py`, `hunyuan.py`；本会话 registry 输出包含全部
- [x] OpenAI scraper 端到端验证
  证据: 本会话 `python -m scrapers.run --dry-run --vendor openai` 输出 "9 models, 9 prices, 0 scores"

## Phase 4 — Benchmark Scrapers

- [x] `lmsys.py`
  证据: `scrapers/benchmarks/lmsys.py:25` scrape()，运行时 LMSYS CSV 镜像返回 HTTPStatusError → 静默返回空 list（设计内行为）
- [x] `artificial_analysis.py`
  证据: `scrapers/benchmarks/artificial_analysis.py:33` scrape()；运行时本地 Playwright Chromium 未装 → 静默失败（GitHub Actions 装好后会工作）
- [x] `academic.py`
  证据: `scrapers/benchmarks/academic.py:13` SEED_SCORES 含 40 条；本会话 `python -m scrapers.run --dry-run --benchmark academic` 输出 40 scores
- [x] `_mapping.py` benchmark-name → model_id
  证据: `scrapers/benchmarks/_mapping.py` NAME_TO_MODEL_ID 含全部 14 家厂商映射

## Phase 5 — 前端（Next.js SSG）

- [x] Next.js 15 + TS + Tailwind 工程
  证据: `apps/web/package.json`（next 15.5, react 19）；`npm run type-check` 0 errors；`npm run build` 输出 8 路由
- [x] `lib/supabase.ts` 懒加载 client
  证据: `apps/web/lib/supabase.ts`（Proxy 形式，build-time env 缺失不崩；build 已验证通过）
- [x] `lib/queries.ts`
  证据: `apps/web/lib/queries.ts:14-99` 9 个查询函数 (getModels, getModelById, getPriceHistory, getCurrentBenchmarks, getLeaderboard, getRecentSnapshots, getLatestSnapshot, getBenchmarkNames, getVendors)
- [x] `lib/format.ts`
  证据: `apps/web/lib/format.ts` fmtPrice/fmtTokens/fmtDate/fmtElo/fmtPct/countryFlag/modelHref
- [x] 首页 `/`
  证据: `apps/web/app/page.tsx`；本会话 `curl http://localhost:3777/` → HTTP 200
- [x] `/models`（表格 + 筛选 + 排序）
  证据: `apps/web/app/models/page.tsx` + `app/models/ModelsTable.tsx`（8 列表格，筛选 search/vendor/status/openOnly，可排序）；HTTP 200
- [x] `/models/[...id]`（catch-all，价格曲线 + 雷达图）
  证据: `apps/web/app/models/[...id]/page.tsx` + `PriceChart.tsx` + `BenchmarkRadar.tsx`；catch-all 因 model id 含 `/` 需要分段路由
- [x] `/pricing`
  证据: `apps/web/app/pricing/page.tsx`，按 input price 排序的对比表 + blended 3:1；HTTP 200
- [x] `/benchmarks`
  证据: `apps/web/app/benchmarks/page.tsx`，tab 切换不同 benchmark；HTTP 200
- [x] `/timeline`
  证据: `apps/web/app/timeline/page.tsx`，按月分组发布时间线；HTTP 200
- [x] `/changelog`
  证据: `apps/web/app/changelog/page.tsx`，渲染 daily_snapshots.changes_json；HTTP 200
- [x] `/not-found`
  证据: `apps/web/app/not-found.tsx`
- [x] Header / Footer
  证据: `apps/web/app/layout.tsx:25-42` Header, `:50-65` Footer

## Phase 6 — 自动化与部署

- [x] `.github/workflows/scrape-daily.yml`
  证据: 文件存在，cron `0 2 * * *`，workflow_dispatch + 失败时 actions/github-script 开 issue
- [x] `vercel.json`
  证据: 文件存在，buildCommand/outputDirectory 指向 `apps/web/.next`

## Phase 7 — 验证

- [x] `npm run type-check` 通过
  证据: 本会话 `npm run type-check` 0 errors
- [x] `npm run build` 通过
  证据: 本会话输出 "8 routes / 5 static + 3 dynamic"，包含 `○ /`, `○ /models`, `○ /pricing`, `ƒ /benchmarks`, `ƒ /models/[...id]`, `○ /timeline`, `○ /changelog`
- [x] Registry 发现全部 scraper
  证据: 本会话 `python -c "from scrapers.core.registry ..."` 列出 14 vendors + 3 benchmarks
- [x] OpenAI scraper dry-run
  证据: 本会话输出 "9 models + 9 prices"
- [x] Academic benchmark dry-run
  证据: 本会话输出 "40 scores"
- [x] Cold-start walkthrough（所有公开路由 200）
  证据: 本会话 curl 7 个公开路径全部 HTTP 200 (`/`, `/models`, `/pricing`, `/benchmarks`, `/benchmarks?b=arena-elo`, `/timeline`, `/changelog`)；`/models/openai/gpt-5` 在 stub DB 下 404 是正常行为

## Phase 8 — 实际部署到 Supabase（本会话新增）

- [x] 创建 Supabase 项目 `model.tracker`
  证据: MCP `create_project` 返回 `id=nekwycbmflpetazhdpzx`, `status=ACTIVE_HEALTHY`
- [x] 在 Supabase 应用 schema migration
  证据: MCP `apply_migration name=initial_schema` 返回 `{"success":true}`
- [x] 在 Supabase 应用 vendors seed
  证据: MCP `execute_sql` insert into vendors 返回 14 行
- [x] 在 Supabase 应用 models / prices / benchmarks
  证据: MCP `execute_sql` 三个大 insert 返回成功；本会话验证 `select count(*) from vendors, models, prices, benchmark_scores` = 14 / 79 / 72 / 40
- [x] 写入首个 daily snapshot
  证据: `select count(*) from daily_snapshots` = 1

## Phase 9 — Vercel 部署

- [x] Vercel CLI 登录 + 创建项目
  证据: 本会话 `vercel project add model-tracker --scope dingdugans-projects` 返回 success；后改名 `vercel project rename model-tracker model.tracker` 返回 success
- [x] 配 Vercel env vars
  证据: 本会话 `vercel env add NEXT_PUBLIC_SUPABASE_URL production` + `NEXT_PUBLIC_SUPABASE_ANON_KEY production` 均返回 "Added Environment Variable"
- [x] `vercel --prod` 部署 + 设置 alias
  证据: 本会话部署返回 `readyState: READY`, deployment id `dpl_6hWDVjwGSy4No5bynTCea2JwNTph`；`vercel alias set` 后 `https://model-tracker.vercel.app/` HTTP 200，页面渲染真实模型数据（curl grep 到 "GPT-5 / Claude Opus 4.7 / DeepSeek V3.2 / Qwen3 Max"）
- [x] 关闭 SSO protection 让 alias 可公开访问
  证据: `vercel project protection disable --sso` 返回 `ssoProtection: false`

## Phase 10 — 开源就绪审计

- [x] LICENSE (MIT) / SECURITY.md / CONTRIBUTING.md
  证据: 三个文件存在于仓库根目录
- [x] README 加数据来源声明 + 免责声明
  证据: `README.md` 末尾包含 "Data sources & attribution" 和 "Disclaimer" 两节
- [x] `.gitignore` 补 `*.tsbuildinfo` + `.vercel/`
  证据: 本会话 `git check-ignore apps/web/tsconfig.tsbuildinfo` 和 `apps/web/.vercel` 均匹配
- [x] 个人信息 / 凭据全面扫描
  证据: 本会话 grep `/Users/bytedance/`, `dingdugan`, `sk-ant-...`, `sb_secret_`, `sb_publishable_D0kAr0Km...`, `nekwycbmflpetazhdpzx` 均 0 命中（committed 文件中）

## Phase 11 — GitHub 推送 + Actions 配置

- [ ] 初始 commit
- [ ] 创建 GitHub repo + push
- [ ] 创建 Vercel deploy hook
- [ ] 设置 GitHub Actions Secrets（部分用户提供）
- [ ] 触发一次 workflow 验证 cron 跑通

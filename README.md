# model.tracker

自动监控全球主流 AI 厂商的模型发布、定价、性能表现。每日更新。

## 覆盖范围

**14 家厂商：**

- 海外：OpenAI · Anthropic · Google · Meta · Mistral · xAI · Cohere
- 国内：DeepSeek · 通义千问（阿里）· 智谱 GLM · 豆包（字节）· Kimi（Moonshot）· 百川 · 混元（腾讯）

**3 类性能数据源：**

- LMSYS Chatbot Arena（人类盲测 Elo）
- Artificial Analysis（独立第三方测速 + 质量）
- 学术 benchmark（MMLU / GPQA / HumanEval / SWE-bench / MATH）

## 架构

```
                   ┌─────────────────────┐
                   │  GitHub Actions     │  每日 02:00 UTC cron
                   │  scrapers/run.py    │
                   └──────────┬──────────┘
                              │
   ① 发现 + 自动晋升           ▼
   ┌──────────────────────────────────────────┐
   │ discovery: 厂商官方 Models API (权威)      │→ 未收录模型 自动入库
   │           + benchmark 榜单 (噪声→仅记录)   │
   └───────────────┬──────────────────────────┘
                   │  register_extra → 统一注册表 (catalog ∪ 自动发现)
   ② 采集           ▼
   ┌──────────────────────────────────────────┐
   │ vendor scrapers  benchmarks  LLM fallback │
   │ (价格/规格)      (Elo/跑分)   (Claude Haiku) │
   └───────────────┬──────────────────────────┘
                   │  归一化精确匹配 (model_registry) — 绝不错配
   ③ 校验闸          ▼
   ┌──────────────────────────────────────────┐
   │ validation: 价格>3× / ELO>100 跳变 → 隔离  │  防脏值覆盖
   │             benchmark 覆盖骤降 → 漂移告警   │
   └───────────────┬──────────────────────────┘
                   ▼
          ┌────────────────┐
          │   Supabase     │  Postgres + RLS
          │  models/prices │  benchmark_scores · daily_snapshots
          │  discovery_*   │  pending_changes · scrape_errors
          └────────┬───────┘
                   ▼
          ┌────────────────┐
          │  Next.js ISR   │  apps/web (含 /health 数据健康页)
          │  on Vercel CDN │  push→git 自动部署；数据靠 ISR 刷新
          └────────────────┘
```

**健壮性设计**（详见 `IMPLEMENTATION_CHECKLIST.md` 的"健壮性大修"章节）：

- **不漏新模型**：厂商官方 Models API 是权威信号，发现未收录模型即**自动入库**（稀疏元数据，价格/Elo 由采集层随后自动补，绝不编造）。arena/AA 榜单名是噪声，**永不自动收**、也不骚扰，仅在 `/health` 页可选查看。
- **不错配**：单一身份注册表（`core/model_registry.py`）从 catalog ∪ 自动发现派生，**归一化精确匹配**（受控地剥离 `-thinking`/日期等模式后缀，绝不剥 size/version），CI 强制无别名碰撞。一个模型只在一处定义。
- **防脏值**：异常闸隔离离谱跳变（曾导致价格来回跳的根因），同值持续 2 次才确认应用。
- **不静默失败**：匹配不上 = 登记为发现候选 + 漂移告警，全在 `/health` 暴露。

## 目录结构

```
apps/web/                 Next.js 前端（含 /health 数据健康页）
scrapers/                 Python 爬虫
  vendors/                每家厂商一个 module（catalog 驱动）
  benchmarks/             LMSYS / Artificial Analysis / 学术
  discovery/              发现层：厂商官方 Models API 等可信源
  core/
    model_registry.py     单一身份注册表（catalog ∪ 自动发现，精确匹配）
    discovery.py          发现过滤 + 厂商推断（纯逻辑）
    promotion.py          自动晋升：可信源 → 模型记录（纯逻辑）
    validation.py         价格/ELO 异常闸（纯逻辑）
    extractor / db / differ / registry
  tests/                  registry / discovery / validation / promotion 单测（CI）
  alert_candidates.py     数据健康告警（隔离值）→ GitHub issue
supabase/migrations/      Postgres schema（0001–0007）
.github/workflows/        scrape-daily（cron）+ test（pytest on PR）
```

## 本地开发

### 前端

```bash
cd apps/web
npm install
cp ../../.env.example .env.local   # 填入 SUPABASE_URL + SUPABASE_ANON_KEY
npm run dev
```

### 爬虫

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scrapers/requirements.txt
playwright install chromium

cp .env.example .env                  # 填入所有 KEY
python -m scrapers.run --dry-run      # 跑一遍但不写库
python -m scrapers.run                # 真跑
python -m scrapers.run --vendor openai     # 只跑一家
python -m scrapers.run --skip-discovery    # 跳过发现/自动晋升
pytest scrapers/tests/                # 跑单测（注册表/发现/校验/晋升）
```

### Supabase

```bash
# 在 https://supabase.com/dashboard 建项目，拿 URL + Service Key
# 在 SQL Editor 按序执行所有 migration，再灌 seed：
#   supabase/migrations/0001_initial.sql            初始 6 表 + 视图 + RLS
#   supabase/migrations/0002_dedupe_benchmarks.sql
#   supabase/migrations/0003_add_model_license.sql
#   supabase/migrations/0004_discovery_candidates.sql  发现候选表
#   supabase/migrations/0005_pending_changes.sql       异常隔离表
#   supabase/migrations/0006_data_health_views.sql     脱敏错误视图
#   supabase/migrations/0007_auto_discovered.sql       models.auto_discovered
#   supabase/seed.sql
```

## 数据 schema

| 表 / 视图 | 说明 |
|---|---|
| `vendors` | 厂商主数据（OpenAI / Anthropic / ...） |
| `models` | 模型主数据，每个模型一行；`auto_discovered` 标记 API 自动晋升 |
| `prices` | 价格快照，追加写，保留全部历史 |
| `benchmark_scores` | 跑分快照，追加写 |
| `daily_snapshots` | 每日汇总 + 当日变化 JSON（含发现候选） |
| `discovery_candidates` | 发现层捞到、尚未收录的模型名（仅提案，按厂商分级） |
| `pending_changes` | 异常闸隔离的可疑值（同值持续 2 次自动确认应用） |
| `scrape_errors` | 爬虫错误日志（含漂移告警） |
| `models_overview` *(视图)* | 模型 + 当前价格 + Arena Elo 聚合，前端读取 |
| `recent_scrape_issues` *(视图)* | `scrape_errors` 脱敏投影（无 traceback/url），供 /health |

## Data sources & attribution

This project aggregates publicly available information from:

- **Vendor pricing pages** — listed in `supabase/seed.sql` per vendor (`pricing_url`)
- **[LMSYS Chatbot Arena](https://lmarena.ai)** — Elo leaderboard
- **[Artificial Analysis](https://artificialanalysis.ai)** — independent third-party benchmarks
- **Official vendor announcements** — for academic benchmark numbers (MMLU / GPQA / HumanEval / SWE-bench / MATH)

Every `prices` and `benchmark_scores` row carries a `source_url` pointing back to the upstream.

## Disclaimer

- **Prices are best-effort.** Always confirm against the vendor's official pricing page before making a procurement decision. Scrapers can miss page changes and the `fallback_prices` baked into vendor files may be stale.
- **Benchmark numbers are reported figures**, not independently re-run. Where vendors and third parties disagree, both are shown when available; trust your own evaluation.
- **No affiliation.** This project is not affiliated with or endorsed by any vendor listed.

## License

[MIT](LICENSE) — see `LICENSE` file. Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Security issues — see [SECURITY.md](SECURITY.md).

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
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        vendor scrapers  benchmarks     LLM fallback
        (selector主路径)   (selector)    (Claude Haiku)
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                     ┌────────────────┐
                     │   Supabase     │  Postgres + RLS
                     │   (prices,     │
                     │   benchmarks,  │
                     │   snapshots)   │
                     └────────┬───────┘
                              │
                              ▼
                     ┌────────────────┐
                     │  Vercel Deploy │  trigger via webhook
                     │  Hook          │
                     └────────┬───────┘
                              ▼
                     ┌────────────────┐
                     │  Next.js SSG   │  apps/web
                     │  on Vercel CDN │
                     └────────────────┘
```

## 目录结构

```
apps/web/                 Next.js 前端
scrapers/                 Python 爬虫
  vendors/                每家厂商一个 module
  benchmarks/             LMSYS / Artificial Analysis / 学术
  core/                   提取器 + Supabase 写入 + 差分
supabase/migrations/      Postgres schema
.github/workflows/        每日 cron
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

cp .env.example .env                # 填入所有 KEY
python scrapers/run.py --dry-run    # 跑一遍但不写库
python scrapers/run.py              # 真跑
python scrapers/run.py --vendor openai   # 只跑一家
```

### Supabase

```bash
# 在 https://supabase.com/dashboard 建项目，拿 URL + Service Key
# 在 SQL Editor 依次执行：
#   supabase/migrations/0001_initial.sql
#   supabase/seed.sql
```

## 数据 schema

| 表 | 说明 |
|---|---|
| `vendors` | 厂商主数据（OpenAI / Anthropic / ...） |
| `models` | 模型主数据，每个模型一行 |
| `prices` | 价格快照，追加写，保留全部历史 |
| `benchmark_scores` | 跑分快照，追加写 |
| `daily_snapshots` | 每日汇总 + 当日变化 JSON |
| `scrape_errors` | 爬虫错误日志 |

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

# Contributing

## 分支命名

```
feat/short-description     # 新功能
fix/what-is-broken         # bug 修复
data/vendor-or-model-name  # catalog / 价格 / benchmark 数据更新
chore/what-is-changed      # 依赖、配置、CI
```

示例：`feat/compare-page`、`fix/lmsys-rsc-parse`、`data/add-grok-5`

## 工作流

```bash
# 1. 从最新 main 开分支
git checkout main && git pull
git checkout -b feat/my-feature

# 2. 改代码，commit
git add -p   # 或 git add <files>
git commit -m "feat: describe what you did"

# 3. 推到 remote，开 PR
git push -u origin feat/my-feature
gh pr create --fill   # 填 PR 模板后提交

# 4. 自己 merge（0 required reviewers，直接 squash merge）
gh pr merge --squash --delete-branch
```

## Commit message 格式

```
<type>: <short description>

type: feat | fix | data | chore | docs | refactor
```

## 注意

- 禁止直接 push 到 `main`（ruleset 已启用，会被拒绝）
- TypeScript 必须零错误（`cd apps/web && npx tsc --noEmit`）
- Python 改动涉及 scraper 的，dry-run 跑一遍再 PR
- 改了模型 catalog / 别名，跑 `pytest scrapers/tests/`（CI 会强制：别名无碰撞、每个模型可 round-trip）

## 新增 / 收录一个模型

- **tracked 厂商的新发布**：通常**无需手动加** —— 厂商官方 Models API 会被发现层自动晋升入库（稀疏元数据，价格/Elo 随后自动补）。
- **想精修元数据 / 收录非 API 暴露的模型**：在 `scrapers/vendors/<vendor>.py` 的 `catalog` 手加一条 `ModelRecord`。
  - 若 benchmark 榜单用了不同显示名，加进该条的 `aliases=[...]`（注册表精确匹配，CI 会确保它能被解析）。
  - 所有具体值（context window / 价格 / 参数量）必须 ground 在厂商真实信息上，缺则留空，**不要编造**。
- **想忽略某个发现候选**：把 `discovery_candidates` 里对应行 `status` 置 `dismissed`。
- 想看流水线现状（自动发现、隔离值、stale 价、未收录名）：`/health` 页。

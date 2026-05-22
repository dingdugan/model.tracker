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

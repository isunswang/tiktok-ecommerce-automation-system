# 贡献指南

## 分支策略

采用 Git Flow 分支模型：

| 分支类型 | 命名规范 | 说明 |
|---------|---------|------|
| main | main | 生产代码，仅通过PR合并 |
| develop | develop | 开发主线 |
| 功能分支 | feature/模块-简述 | 功能开发 |
| 修复分支 | hotfix/简述 | 紧急修复 |
| 发布分支 | release/v版本号 | 发布准备 |

## 代码规范

### Python

- 格式化：`black`（行宽120）+ `isort`
- 类型检查：`mypy --strict`
- Lint：`flake8`（max-line-length=120）
- 导入：绝对导入，禁止通配符导入
- 类型注解：所有函数参数和返回值必须标注
- 金额：一律使用 `Decimal`，禁止 `float`
- 异步：IO密集操作使用 `async/await`

### TypeScript/Vue

- 格式化：Prettier（单引号、2空格缩进）
- Lint：ESLint + @vue/eslint-config-typescript
- 组件命名：PascalCase（如 `ProductList.vue`）
- 组合式API：使用 `<script setup>` 语法
- 状态管理：Pinia

### 代码提交

- 格式：`type(scope): description`
- type: feat/fix/docs/style/refactor/test/chore
- 示例：`feat(product): add 1688 scraping API`

## PR规范

1. 从 develop 创建 feature 分支
2. 单元测试覆盖率 >= 80%（核心逻辑 100%）
3. 通过 `make lint` 和 `make test`
4. PR描述包含：变更说明、测试方法、影响范围
5. 至少1人Code Review

## 人工干预规则

仅以下场景需人工审批：

| 等级 | 场景 | 审批人 |
|------|------|--------|
| P0 | 生产部署、数据库迁移、安全漏洞 | CTO |
| P1 | 架构变更、支付逻辑、财务规则 | 对应负责人 |
| P2 | 核心功能开发、性能优化 | 知会确认 |
| P3 | 常规开发、文档更新 | 自主执行 |

---
name: 生成TikTok跨境电商全自动运营系统PRD文档
overview: 基于已完成的详细需求说明书，生成标准产品PRD文档，包含9大章节：产品概述、用户角色、业务流程、功能需求、非功能需求、原型说明、验收标准、上线计划、风险方案。
todos:
  - id: read-existing-docs
    content: 读取并分析现有的详细需求文档及两个附录
    status: completed
  - id: create-product-overview
    content: 编写产品概述章节（定位、目标、范围、核心价值）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-user-roles
    content: 整理用户角色与权限章节（复用现有角色矩阵）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-process-flow
    content: 绘制核心业务流程Mermaid图（整合10个子流程）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-functional-requirements
    content: 编写功能需求章节（14大模块+优先级P0/P1/P2）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-nonfunctional-requirements
    content: 编写非功能需求章节（性能/安全/合规/可扩展）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-prototype-spec
    content: 设计原型说明章节（5个核心页面交互逻辑）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-acceptance-criteria
    content: 整合验收标准章节（引用附录A量化指标）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-launch-plan
    content: 编写上线计划与里程碑（4阶段细化时间节点）
    status: completed
    dependencies:
      - read-existing-docs
  - id: create-risk-plan
    content: 整合风险与应对方案章节（引用附录B）
    status: completed
    dependencies:
      - read-existing-docs
  - id: compile-prd-document
    content: 使用[skill:docx]生成完整PRD文档
    status: completed
    dependencies:
      - create-product-overview
      - create-user-roles
      - create-process-flow
      - create-functional-requirements
      - create-nonfunctional-requirements
      - create-prototype-spec
      - create-acceptance-criteria
      - create-launch-plan
      - create-risk-plan
---

## 产品PRD需求概述

基于《TikTok跨境电商全自动运营系统-详细需求说明书V1.0.md》及其附录，生成一份标准的产品需求文档（PRD），包含以下9个章节：

1. **产品概述**：提炼产品定位、目标市场、核心价值、产品边界
2. **用户角色与权限**：定义系统角色（老板/运营/财务/客服等）及其权限矩阵
3. **核心业务流程图**：绘制从1688商品抓取→智能处理→TikTok上架→订单履约→财务核算的全链路流程图
4. **功能需求**：整合14大功能模块，标注P0/P1/P2优先级（P0为MVP核心功能）
5. **非功能需求**：性能指标、安全要求、合规要求、可扩展性设计
6. **原型说明**：描述5个核心页面（选品中心、商品管理、订单中心、数据看板、风控中心）的交互逻辑
7. **验收标准**：整合附录A的可量化验收指标（功能/性能/安全/体验）
8. **上线计划与里程碑**：制定4阶段实施路线图，明确时间节点（MVP→AI升级→全链路→规模化）
9. **风险与应对方案**：整合附录B的技术/业务/市场/组织风险及应急预案

需要补充的内容：

- 产品概述章节（提炼现有内容）
- 原型说明章节（新增页面交互设计）
- 上线计划章节（细化时间节点和里程碑）

文档输出格式：Markdown，结构清晰，图表结合

## 技术实施方案

### 文档架构设计

采用分层文档结构：

- 主文档：PRD核心内容（9大章节）
- 引用附录：现有验收标准和风险评估文档
- 新增原型设计：使用Mermaid绘制页面流程图

### 内容生成策略

1. **产品概述**：从详细需求文档第1、2章提炼产品定位、目标用户、核心价值、竞争优势
2. **用户角色与权限**：直接复用第2.2节的角色矩阵表
3. **核心业务流程**：将第3.2节的10个子流程整合为1个全链路Mermaid流程图
4. **功能需求**：整合第4章的14个模块，补充P0/P1/P2优先级定义
5. **非功能需求**：复用第5章的性能/安全/合规指标
6. **原型说明**：新增章节，设计5个核心页面的交互流程
7. **验收标准**：引用附录A的核心量化指标
8. **上线计划与里程碑**：基于附录B实施路线图，细化时间节点和交付物
9. **风险与应对方案**：引用附录B的风险矩阵和应急预案

### 工具使用

使用`docx` skill创建Word格式PRD文档，确保专业排版和可编辑性

## 使用的Agent Extensions

### docx Skill

- **用途**：创建专业的Word格式PRD文档，包含表格、流程图、标题样式、页眉页脚
- **预期结果**：生成格式规范、可直接用于评审的PRD文档（.docx格式）

### 无需其他扩展

本任务主要为文档整理和内容重组，无需使用code-explorer或其他技能
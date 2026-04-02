-- TikTok跨境电商全自动运营系统 - PostgreSQL初始化脚本
-- 创建扩展、默认角色和基础权限

-- 启用必要扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 设置时区
SET timezone = 'Asia/Shanghai';

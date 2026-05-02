## 商品质量溯源系统 · 后端（Flask + MySQL）

本后端与仓库内两个前端项目接口对齐：

- `commodity-system-user/src/api/*`
- `commodity-system-admin/src/api/*`

统一响应格式：

```json
{ "code": 0, "message": "ok", "data": {} }
```

### 1) 安装依赖

建议创建虚拟环境后安装：

```bash
cd commodity-backend
pip install -r requirements.txt
```

### 2) 配置 MySQL

创建数据库（示例）：

- 数据库名：`commodity_quality`

配置连接字符串（两种方式任选其一）：

- 复制 `.env.example` 为 `.env` 并修改 `DATABASE_URL`
- 或直接设置环境变量 `DATABASE_URL`

示例：

```bash
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/commodity_quality?charset=utf8mb4
```

### 3) 启动后端

Windows 推荐直接一键启动：

```bash
# 双击 run.bat 或者在终端执行
.\run.ps1
```

`run.ps1` 会自动执行：

- 创建虚拟环境（首次）
- 安装依赖
- 从 `DATABASE_URL` 自动创建 MySQL 数据库（`CREATE DATABASE IF NOT EXISTS`）
- 启动 Flask

常用参数：

```bash
# 跳过自动建库（你想手动建库时）
.\run.ps1 -SkipDbInit

# 强制重装依赖
.\run.ps1 -Reinstall

# 不使用 .venv，直接用系统 Python
.\run.ps1 -NoVenv
```

```bash
python app.py
```

默认端口 `5000`，前端通过 Vite 代理访问 `/api/*`。

首次启动会自动：

- `db.create_all()` 建表
- `seed_if_empty()` 写入演示数据（用于看板联调）

种子账号：

- 管理员：`admin / admin123`
- 用户：`demo / demo123`

### 4) ABSA 模型说明

默认开启启发式模式（不下载模型）：

```bash
USE_MOCK_ABSA=1
```

如需使用 transformers 模型推理：

```bash
USE_MOCK_ABSA=0
ABSA_MODEL=tabularisai/multilingual-sentiment-analysis
```


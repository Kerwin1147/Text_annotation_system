# 📝 文本标注系统

一个基于 Flask 的智能文本标注系统，支持中文分词、词性标注（12种）和命名实体识别（5种）。

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特性

### 📁 任务管理
- 支持 `.txt` 和 `.csv` 格式文件上传
- 支持手动输入文本内容
- 任务状态管理（未开始 / 进行中 / 已完成）
- 标注结果导出（JSON 格式）

### 🤖 智能标注
- **中文分词**：基于 jieba 的精准分词
- **词性标注**：自动识别 12 种词性
- **实体识别**：自动识别 5 种命名实体
- **文本分类**：智能判断文本类别（10种）
- **情感分析**：分析文本情感倾向

### ✏️ 手动标注
- **双模式切换**：分词模式 / 实体模式
- **词性修改**：点击词语快速修改词性
- **词语合并**：Ctrl+点击多选后合并
- **实体标注**：选中文本添加为实体
- **实体编辑**：修改实体类型或删除

### 📚 知识库管理
- 自动学习标注实体到知识库
- 手动添加/删除实体
- 搜索和筛选功能
- 导出知识库（JSON 格式）

### 📊 数据统计
- 标注进度统计
- 实体类型分布图表
- 词性分布统计

## 🏷️ 支持的标注类型

### 命名实体类型（5种）

| 类型 | 说明 | 示例 |
|------|------|------|
| 👤 人名 | 人物名称 | 张三、李四、习近平 |
| 📍 地名 | 地点名称 | 北京、上海、纽约 |
| 🏢 组织机构 | 机构名称 | 清华大学、阿里巴巴 |
| 📅 时间日期 | 时间信息 | 2024年、今天、下周一 |
| 💲 数值金额 | 数值或金额 | 100元、50%、1000万 |

### 词性标注类型（12种）

| 分类 | 词性 | 代码 |
|------|------|------|
| **实词** | 名词、动词、形容词、数词、量词、代词、时间词 | n, v, a, m, q, r, t |
| **虚词** | 副词、介词、连词、助词、标点 | d, p, c, u, w |

### 文本分类（10种）

新闻时事、科技数码、财经金融、体育运动、娱乐影视、教育学术、法律法规、医疗健康、生活服务、其他

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **后端框架** | Python 3.7+, Flask 3.0 |
| **数据库** | SQLite + SQLAlchemy ORM |
| **NLP处理** | jieba（分词）, SnowNLP（情感分析） |
| **前端UI** | Bootstrap 5, Bootstrap Icons |
| **数据可视化** | Chart.js |
| **架构模式** | MVC + RESTful API |

## 🚀 快速开始

### 环境要求

- Python 3.7 或更高版本
- pip（Python 包管理工具）
- 现代浏览器（Chrome、Firefox、Edge）

### 安装步骤

#### 1. 克隆项目

    git clone https://github.com/your-username/text-annotation-system.git
    cd text-annotation-system

#### 2. 创建虚拟环境（推荐）

    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

#### 3. 安装依赖

    pip install -r requirements.txt

#### 4. 启动应用

    python run.py

#### 5. 访问系统

打开浏览器访问：http://127.0.0.1:5000

## 📖 使用指南

### 创建标注任务

1. 点击首页「新建任务」按钮
2. 选择「上传文件」或「手动输入」
3. 上传 .txt/.csv 文件或输入文本内容
4. 点击提交创建任务

### 进行标注

1. 在任务列表点击「进入标注」
2. 点击「智能标注」进行自动标注
3. 切换「分词模式」或「实体模式」进行手动调整
4. 点击「保存标注」将结果写入数据库

### 分词模式操作

- **单击词语**：打开词性编辑框
- **Ctrl+单击**：多选词语
- **点击合并**：将选中词语合并为一个

### 实体模式操作

- **选中文本**：弹出添加实体对话框
- **单击实体**：打开编辑/删除对话框

### 导出结果

1. 将任务标记为「已完成」
2. 点击「导出标注」下载 JSON 文件

## 📂 项目结构

    text-annotation-system/
    ├── app/                        # 应用主目录
    │   ├── __init__.py            # 应用工厂函数
    |   ├── config.py              # 配置文件
    │   ├── models.py              # 数据库模型
    │   ├── views.py               # 视图路由
    │   ├── api.py                 # API 接口
    │   ├── utils.py               # 工具函数（NLP处理）
    │   └── templates/             # HTML 模板
    │       ├── layout.html        # 基础布局
    │       ├── index.html         # 首页（任务管理）
    │       ├── annotate.html      # 标注页面
    │       ├── stats.html         # 统计页面
    │       └── knowledge_base.html # 知识库页面
    ├── instance/                   # 实例文件夹
    │   └── annotation.db          # SQLite 数据库
    ├── run.py                      # 启动入口
    ├── requirements.txt            # Python 依赖
    └── README.md                   # 项目说明

## 🔧 CLI 命令

    # 初始化数据库
    python run.py init_db

    # 重置数据库（危险操作）
    python run.py reset_db

    # 添加示例知识库数据
    python run.py seed_knowledge

    # 显示系统统计信息
    python run.py show_stats

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/smart_annotate/<file_id>` | 智能标注 |
| POST | `/api/save_all_annotations` | 保存标注 |
| POST | `/api/clear_annotations/<file_id>` | 清空标注 |
| DELETE | `/api/delete_file/<file_id>` | 删除文件 |
| POST | `/api/mark_complete/<file_id>` | 标记完成 |
| GET | `/api/export_annotations/<file_id>` | 导出标注 |
| POST | `/api/update_word_pos` | 更新词性 |
| POST | `/api/merge_words` | 合并词语 |
| POST | `/api/add_entity` | 添加实体 |
| POST | `/api/update_entity/<entity_id>` | 更新实体 |
| DELETE | `/api/delete_entity/<entity_id>` | 删除实体 |
| GET | `/api/knowledge/entities` | 获取知识库 |
| POST | `/api/knowledge/add` | 添加知识实体 |
| DELETE | `/api/knowledge/delete/<entity_id>` | 删除知识实体 |
| GET | `/api/knowledge/export` | 导出知识库 |
| GET | `/api/stats` | 获取统计信息 |
| POST | `/api/knowledge/batch_delete` | 批量删除知识实体 |
| GET | `/api/pos-tags` | 获取词性标签列表 |
| GET | `/api/entity-types` | 获取实体类型列表 |

## 🖼️ 界面预览

### 任务管理页面
- 统计卡片展示任务状态
- 任务列表支持搜索筛选
- 快捷操作按钮

### 标注页面
- 左侧：文本内容区（支持双模式切换）
- 右侧：词语/实体列表
- 底部：文本分类和情感标注

### 数据统计页面
- 柱状图：标注类别分布
- 饼图：类别占比
- 进度条：各类型详情

### 知识库页面
- 左侧：添加实体表单
- 右侧：实体列表（支持搜索）

## ⚠️ 注意事项

1. **保存标注**：智能标注后需点击「保存标注」才会写入数据库
2. **文件编码**：系统自动检测文件编码，支持 UTF-8、GBK 等
3. **实体重叠**：同一位置不能标注多个实体
4. **词语合并**：只能合并连续的词语

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (git checkout -b feature/AmazingFeature)
3. 提交更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 提交 Pull Request

## 📄 开源协议

本项目采用 MIT 协议开源，详见 LICENSE 文件。

## 👥 开发团队

软件课程设计 - 分组3

## 📮 问题反馈

如有问题或建议，请提交 Issue。
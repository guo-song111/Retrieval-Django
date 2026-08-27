# 人员取物路径可视化系统

这是一个基于 Django、MySQL 和高德地图 JavaScript API 的人员取物路径可视化系统。系统支持 TXT 路径数据导入、路径列表查看、轨迹点展示、多路径叠加、轨迹点说明查看和路径删除。

## 一、技术栈

- 后端：Python 3.14、Django 6.1
- 数据库：MySQL 8.4
- 前端：Django 模板、原生 JavaScript、CSS
- 地图：高德地图 JavaScript API 2.0
- 依赖管理：uv
- 数据库容器：Docker Compose

## 二、项目结构

```text
Retrieval/
├── config/                         Django 项目配置和首页视图
├── pickup_routes/                  取物路径业务模块
│   ├── migrations/                 数据库迁移文件
│   ├── services/                   TXT 解析和数据导入服务
│   ├── models.py                   路径和轨迹点模型
│   ├── urls.py                     接口路由
│   ├── views.py                    JSON 接口视图
│   └── test_*.py                   后端测试
├── static/
│   ├── css/app.css                 页面样式
│   └── js/app.js                   页面交互和地图逻辑
├── templates/index.html            地图首页模板
├── docker-compose.yml              MySQL 容器配置
├── manage.py                       Django 管理命令入口
├── pyproject.toml                  项目依赖和 Python 版本
└── .env.example                    环境变量示例
```

## 三、环境准备

请先安装以下软件：

- Python 3.14
- uv
- Docker Desktop
- Git

检查安装结果：

```powershell
python --version
uv --version
docker --version
git --version
```

## 四、配置环境变量

在项目根目录复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，至少填写数据库密码和高德地图配置：

```dotenv
DJANGO_SECRET_KEY=请替换为随机密钥
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

MYSQL_DATABASE=retrieval
MYSQL_USER=retrieval_user
MYSQL_PASSWORD=开发数据库密码
MYSQL_ROOT_PASSWORD=数据库管理员密码
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307

AMAP_JS_KEY=高德Web端JavaScript密钥
AMAP_SECURITY_JS_CODE=高德安全密钥
```

`.env` 包含密码和地图密钥，已被 Git 忽略，不能提交到版本库。`.env.example` 只能保留空值或说明文字。

## 五、安装依赖并启动数据库

在项目根目录执行：

```powershell
uv sync
docker compose up -d
docker compose ps
```

看到 `retrieval-mysql` 状态为 `healthy` 后，执行数据库迁移：

```powershell
uv run python manage.py migrate
```

## 六、启动开发服务器

```powershell
uv run python manage.py check
uv run python manage.py runserver 127.0.0.1:8001
```

浏览器访问：

```text
http://127.0.0.1:8001/
```

如果 `8001` 已被占用，可以换用其他端口。修改 `.env` 后必须重新启动 Django 服务。

## 七、前端使用方法

1. 打开首页后，系统自动加载路径列表。
2. 选择 TXT 文件，可选填写路径名称，然后点击“导入路径”。
3. 点击路径名称查看该路径的轨迹点表格。
4. 勾选多个路径，可在地图上同时查看不同颜色的路线。
5. 将鼠标移动到地图轨迹点上，可查看状态和说明信息。
6. 选择当前路径并点击“删除当前路径”，确认后会同时删除该路径的轨迹点。

没有配置高德密钥时，路径列表和导入功能仍可使用，但地图区域会显示配置提示。

## 八、TXT 文件格式

一个 TXT 文件代表一条取物路径，每行代表一个轨迹点。文件必须使用 UTF-8 编码，字段使用制表符分隔：

```text
经度    纬度    轨迹点说明    状态
121.473700    31.230400    一号物品，数量1    notget
121.475100    31.232000    二号物品，数量2    carrier
```

状态只能是：

- `carrier`：物品已取
- `notget`：物品未取

单个文件大小不能超过 5 MB。一个文件导入后生成一条路径和对应的多个轨迹点。

## 九、接口说明

接口基础路径为 `/api/v1/`。

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/routes/` | 获取路径列表 |
| GET | `/api/v1/routes/{id}/` | 获取路径详情和轨迹点 |
| POST | `/api/v1/routes/import/` | 上传 TXT 并导入路径 |
| DELETE | `/api/v1/routes/{id}/` | 删除路径及其轨迹点 |

POST 和 DELETE 需要 Django CSRF Token。前端页面会自动读取隐藏字段并发送 `X-CSRFToken` 请求头。

## 十、数据表和数据流转

系统主要包含两张业务表：

- `pickup_route`：保存路径名称、原始文件名、文件摘要、颜色和导入时间。
- `route_point`：保存经度、纬度、说明、状态和路径内的顺序。

数据流转过程如下：

```text
TXT 文件
  -> route_parser.py 解析和校验
  -> route_importer.py 事务写入 MySQL
  -> JSON 接口返回路径数据
  -> app.js 请求数据并绘制高德地图
```

路径删除使用外键级联关系，删除路径时会自动删除其轨迹点。坐标按高德地图 GCJ-02 坐标系处理，前端不重复转换。

## 十一、测试和代码检查

```powershell
uv run python manage.py test pickup_routes config
uv run python manage.py check
git diff --check
```

前端 JavaScript 语法检查：

```powershell
node --check static/js/app.js
```

## 十二、常见问题

### 1. 页面显示“高德密钥未配置”

确认真实配置写在项目根目录 `.env`，变量名拼写正确，然后停止并重新启动 Django 服务。不要把密钥只写在 `.env.example` 中。

### 2. 地图提示 Key 无效

检查高德控制台中的 Web 端 JavaScript API Key、Security Code 和域名白名单。开发环境可以添加 `http://127.0.0.1:8001` 和 `http://localhost:8001`。

### 3. MySQL 无法连接

执行 `docker compose ps`，确认 `retrieval-mysql` 为 `healthy`，并确认 `.env` 中 `MYSQL_PORT=3307` 与 Docker Compose 端口映射一致。

### 4. 端口被占用

使用其他端口启动，例如：

```powershell
uv run python manage.py runserver 127.0.0.1:8002
```

## 十三、Git 提交建议

查看状态和提交记录：

```powershell
git status
git log --oneline --decorate -5
```

提交代码前确认 `.env` 没有出现在 `git status` 中，也没有把真实密钥写入 `.env.example`。


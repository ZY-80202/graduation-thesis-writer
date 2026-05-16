# graduation-thesis-writer

这是一个本地运行的 Python MVP 工具，用于从学校 Word 模板、上一届优秀论文和你的项目资料中提取结构信息，并生成一份可继续人工修改的毕业设计说明书 Word 文档。

> 注意：上一届论文只用于参考结构、格式、章节组织方式和写作模式。工具不会把上一届正文写入新论文，并会生成查重风险报告，提醒需要人工改写的位置。

## 作为 Codex Skill 安装

克隆到 Codex skills 目录即可：

```bash
git clone https://github.com/<your-name>/graduation-thesis-writer.git ~/.codex/skills/graduation-thesis-writer
```

Windows PowerShell 示例：

```powershell
git clone https://github.com/<your-name>/graduation-thesis-writer.git $env:USERPROFILE\.codex\skills\graduation-thesis-writer
```

安装后重启或刷新 Codex，然后可以直接说：

```text
使用 graduation-thesis-writer，根据 inputs/template.docx、inputs/previous.docx 和 inputs/project/ 生成毕业论文。
```

## 安装

```bash
pip install -r requirements.txt
```

在 Windows 上如果 `python` 命令不可用，可以使用：

```bash
py -m pip install -r requirements.txt
```

如果作为 Codex Skill 使用，内置工具也在：

```text
scripts/thesis_tool/
```

可以通过设置 `PYTHONPATH` 调用内置工具：

```powershell
$env:PYTHONPATH=".\scripts\thesis_tool"
py -m graduation_thesis_writer --help
```

## 输入文件

建议目录如下：

```text
inputs/
├── template.docx
├── previous.docx
├── previous.pdf
└── project/
    ├── 项目说明.md
    ├── requirements.txt / package.json / pom.xml
    ├── database.sql
    ├── screenshots/
    ├── source_code/
    │   ├── backend/
    │   └── frontend/
    └── src/
```

项目资料目录支持 `.txt`、`.md`、`.docx`、`.xlsx`、`.csv`、`.sql` 以及常见前后端源码文件。截图支持 PNG、JPG、BMP、WEBP 等格式。
建议把后端路由、Controller 或 API 文件放在 `source_code/backend/`，把前端页面文件放在 `source_code/frontend/`，把系统截图放在 `screenshots/`。截图文件名可以包含 `login`、`user`、`product`、`order`、`admin`、`test` 等关键词，工具会据此判断插入章节。

## 常用命令

分析学校模板：

```bash
python -m graduation_thesis_writer inspect-template --template inputs/template.docx
```

分析上一届论文：

```bash
python -m graduation_thesis_writer inspect-previous --docx inputs/previous.docx --pdf inputs/previous.pdf
```

分析项目资料：

```bash
python -m graduation_thesis_writer inspect-project --project inputs/project/
```

生成论文大纲：

```bash
python -m graduation_thesis_writer build-outline --template inputs/template.docx --previous inputs/previous.docx --project inputs/project/
```

生成流程图：

```bash
python -m graduation_thesis_writer build-diagrams --project inputs/project/ --out outputs/diagrams/
```

生成完整论文：

```bash
python -m graduation_thesis_writer build \
  --template inputs/template.docx \
  --previous-docx inputs/previous.docx \
  --previous-pdf inputs/previous.pdf \
  --project inputs/project/ \
  --out outputs/final_thesis.docx
```

检查论文格式：

```bash
python -m graduation_thesis_writer validate --docx outputs/final_thesis.docx --template inputs/template.docx
```

## 输出文件

所有输出默认放在 `outputs/`：

- `outputs/final_thesis.docx`：生成的毕业设计 Word 文档；
- `outputs/profiles/template_profile.json`：模板格式分析结果；
- `outputs/profiles/previous_profile.json`：上一届论文结构分析结果；
- `outputs/profiles/project_profile.json`：项目资料分析结果；
- `outputs/profiles/outline.json`：论文目录结构；
- `outputs/diagrams/`：自动生成的 PNG、SVG 和 Mermaid 图；
- `outputs/content_gap_report.md`：内容缺失项提醒；
- `outputs/missing_items.md`：需要人工补充的内容；
- `outputs/format_check_report.md`：格式检查报告；
- `outputs/plagiarism_risk_report.md`：查重风险提醒。

## 配置

修改 `config.yaml` 可以配置论文题目、作者、学号、学院、专业、指导教师、项目名称、技术栈、图表编号规则和格式要求。

示例：

```yaml
thesis:
  title: "校园二手交易系统的设计与实现"
  author: "张三"
  student_id: "2024000001"
  college: "信息工程学院"
  major: "软件工程"
  supervisor: "李老师"
  project_name: "校园二手交易系统"
```

## 当前 MVP 能力

- 读取 Word 模板页面设置、页眉页脚、常见段落样式和区域关键词；
- 读取上一届 Word/PDF，提取目录、章节层级和图表编号规律；
- 读取项目资料，识别技术栈、模块、角色、数据表、接口、截图和测试点；
- 根据 `database.sql` 自动整理数据库设计章节，并生成字段说明表；
- 根据 `source_code/backend/` 中的路由文件生成接口设计表；
- 根据 `source_code/frontend/` 中的页面文件生成系统功能页面表；
- 根据 `screenshots/` 图片名称自动匹配功能章节并插入 Word；
- 用户用例图和管理员用例图采用 UML 风格：左侧角色小人、右侧系统边界、内部椭圆用例和箭头连线；
- 自动生成七章式毕业设计目录，可根据项目模块替换第 5 章小节；
- 自动生成系统架构图、功能结构图、业务流程图、ER 图、交互流程图和测试流程图；
- 基于学校模板样式生成 Word 文档，并插入目录域、图、表和待补充标记；
- 输出格式检查、内容缺失项和查重风险报告。

## 简化说明与后续增强

当前版本优先保证可运行和可重复生成，因此部分能力是简化实现：

- 模板封面会继承模板样式和页面设置，但不会智能填充复杂封面控件；
- Word 目录插入为可更新目录域，需要在 Word 中右键更新域；
- 图表为黑白简洁风格，适合论文初稿，复杂 ER 关系需要结合实际外键继续完善；
- 正文生成是基于项目资料的规则化草稿，不会替代人工核对、补充截图和参考文献；
- 格式检查覆盖基础项，学校特定格式细则可继续扩展到 `format_validator.py`。

## 常见问题

**生成内容里有【请补充】怎么办？**  
这表示项目资料不足或工具无法可靠判断，建议按 `content_gap_report.md` 补充资料后重新运行。

**上一届论文会不会被复制？**  
不会。上一届论文分析只输出结构 profile，不把正文放进新论文。生成后会额外输出 `plagiarism_risk_report.md`。

**为什么目录页没有页码？**  
工具插入的是 Word TOC 域。打开 Word 后右键目录，选择更新域即可。

**没有 Graphviz 能生成图吗？**  
可以。MVP 默认用 Pillow 生成 PNG，并写出 SVG 和 Mermaid 文件，不依赖本机 Graphviz。

## 兼容入口

Python 模块名不能使用连字符，因此本地推荐命令使用下划线形式：

```bash
python -m graduation_thesis_writer --help
```

旧入口仍然可用：

```bash
python -m thesis_skill --help
```

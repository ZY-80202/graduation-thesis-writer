from __future__ import annotations

from typing import Iterable, List

from thesis_skill.models import OutlineSection, ProjectProfile, SectionDraft


def generate_sections(outline: List[OutlineSection], project: ProjectProfile) -> List[SectionDraft]:
    return [_generate_section(section, project) for section in outline]


def _generate_section(section: OutlineSection, project: ProjectProfile) -> SectionDraft:
    paragraphs = _paragraphs_for(section, project)
    return SectionDraft(
        number=section.number,
        title=section.title,
        level=section.level,
        paragraphs=paragraphs,
        children=[_generate_section(child, project) for child in section.children],
    )


def _paragraphs_for(section: OutlineSection, project: ProjectProfile) -> List[str]:
    key = f"{section.number} {section.title}"
    stack = "、".join(project.technology_stack) or "【请补充项目技术栈】"
    modules = "、".join(project.function_modules[:8]) or "【请补充主要功能模块】"
    roles = "、".join(project.user_roles) or "普通用户、管理员【请核对用户角色】"
    tables = "、".join(table.name for table in project.database_tables[:8]) or "【请补充数据库表】"
    pages = "、".join(project.frontend_pages[:8]) or "【请补充前端页面】"
    project_name = project.project_name or "本系统"

    generators = [
        ("研究背景", lambda: [f"随着信息化应用在日常管理和业务处理中的普及，{project_name}需要通过软件系统对业务数据、用户操作和管理流程进行统一支撑。项目资料显示，系统围绕{modules}等功能展开，目标是减少人工处理成本，提高信息流转效率。"]),
        ("研究意义", lambda: [f"本课题的意义主要体现在两个方面：一是结合实际业务场景完成{project_name}的需求分析、设计、实现与测试；二是通过{stack}等技术完成完整的软件开发过程，为类似场景的信息化建设提供可复用的实现经验。"]),
        ("国内外研究现状", lambda: ["同类系统通常围绕用户身份认证、数据维护、业务流程处理和统计查询等能力建设。成熟系统更关注权限控制、数据一致性、可维护性和良好的交互体验。本文不直接比较商业产品功能细节，而是结合本项目资料，说明系统在业务流程、模块划分和数据设计上的实现方案。【请补充与你课题相关的文献综述】"]),
        ("研究内容", lambda: [f"本文围绕{project_name}开展研究与实现，主要内容包括：梳理系统业务需求，设计系统总体架构与功能模块，完成数据库表结构和接口设计，实现{modules}等功能，并通过功能测试验证系统主要流程。"]),
        ("论文组织结构", lambda: ["全文共分为七章。第一章介绍研究背景和研究内容；第二章说明系统相关技术；第三章进行需求分析；第四章给出总体设计；第五章说明详细设计与实现；第六章介绍系统测试；第七章总结工作并提出后续改进方向。"]),
        ("前端开发技术", lambda: [f"系统前端部分主要用于承载用户交互、页面展示和表单提交。根据项目资料，前端技术栈包括{stack}，识别到的主要页面包括{pages}。在实现过程中，前端页面需要与后端接口保持一致的数据格式，并对关键输入进行基础校验，以提升操作体验和数据提交质量。"]),
        ("后端开发技术", lambda: [f"后端部分负责业务逻辑处理、数据校验、权限控制和数据库访问。项目采用的相关技术包括{stack}，当前从路由文件中识别到 {len(project.backend_endpoints)} 个接口。后端实现应重点保证接口职责清晰、异常处理明确，并通过分层结构降低业务模块之间的耦合。"]),
        ("数据库技术", lambda: [f"数据库用于保存系统运行过程中的核心业务数据。当前识别到的主要数据表包括{tables}。数据库设计需要关注主键、字段约束、字段说明和常用查询字段，以保证数据完整性和查询效率。"]),
        ("系统开发环境", lambda: [f"系统开发环境由开发语言、框架、数据库和运行工具组成。项目资料识别的技术栈为{stack}。具体版本号、开发工具、操作系统和部署环境建议在最终提交前根据实际机器环境补充完整。"]),
        ("可行性分析", lambda: [f"从技术可行性看，{stack}能够支撑系统主要功能开发；从操作可行性看，系统面向{roles}，交互流程以常规业务操作为主，学习成本较低；从经济可行性看，项目以本地开发和常见开源技术为基础，整体实现成本可控。"]),
        ("功能需求分析", lambda: [f"系统功能需求围绕{roles}展开，核心模块包括{modules}。各模块需要完成数据录入、查询、修改、删除、状态流转或统计展示等操作，并保证用户只能访问其权限范围内的功能。"]),
        ("非功能需求分析", lambda: ["系统除满足基本功能外，还需要满足可用性、可靠性、安全性和可维护性要求。可用性方面应保证页面提示清晰、流程完整；可靠性方面应对异常输入和接口错误进行处理；安全性方面应关注登录认证、权限控制和敏感数据保护；可维护性方面应保持模块划分清楚、命名规范。"]),
        ("系统业务流程分析", lambda: [f"系统业务流程通常从用户登录开始，用户根据角色进入对应功能模块，提交或查询业务数据，后端完成校验和持久化处理，最终向前端返回处理结果。项目资料中的业务流程可概括为：{'、'.join(project.business_flows) if project.business_flows else '【请补充业务流程】'}。", "【请插入系统业务流程图】"]),
        ("系统架构设计", lambda: [f"系统总体上可按表示层、业务逻辑层和数据访问层进行组织。表示层负责页面展示和用户输入，业务逻辑层负责处理{modules}等业务规则，数据访问层负责与数据库表{tables}进行交互。", "【请插入系统总体架构图】"]),
        ("功能模块设计", lambda: [f"系统功能模块根据用户角色和业务流程进行划分，主要包括{modules}。模块之间通过接口和数据表进行协作，既保证功能边界清晰，也便于后续维护和扩展。", f"前端页面识别结果显示，系统包含{pages}等页面，后续实现章节会结合截图和页面文件说明主要功能。", "【请插入系统功能结构图】"]),
        ("数据库设计", lambda: _database_design_paragraphs(project, tables)),
        ("接口设计", lambda: [f"接口设计用于连接前端页面与后端业务逻辑。系统接口应统一请求路径、请求方法、参数格式和返回结构。当前自动识别到 {len(project.backend_endpoints)} 个接口路径，接口表将列出请求方法、接口路径、接口说明和来源文件。", "【请补充核心接口请求参数和返回示例】"]),
        ("测试环境", lambda: [f"系统测试环境应与开发环境保持一致或尽量接近。根据项目资料，测试所涉及的技术环境包括{stack}。测试前需要准备数据库初始数据、用户账号以及典型业务场景数据。"]),
        ("测试方法", lambda: ["本文主要采用功能测试和黑盒测试方法，对登录认证、核心业务流程、数据增删改查、异常输入处理等内容进行验证。对于关键接口，可结合接口调试工具检查请求参数、响应状态和返回数据。", "【请插入系统测试流程图】"]),
        ("功能测试", lambda: [f"功能测试围绕{modules}展开，重点验证每个模块在正常输入、异常输入和边界情况下的处理结果。测试过程应记录测试步骤、测试数据、预期结果和实际结果。"]),
        ("测试结果分析", lambda: ["从测试结果看，系统主要功能应能够按照需求完成业务处理，常见异常输入能够得到提示或拦截。对于测试中发现的问题，需要记录原因和修复方式，并在最终版本中再次回归验证。【请补充实际测试结论】"]),
        ("工作总结", lambda: [f"本文完成了{project_name}的需求分析、总体设计、详细设计、编码实现和系统测试。系统围绕{modules}等功能展开，能够支撑基本业务流程，并形成了数据库设计、接口设计和测试说明等文档内容。"]),
        ("不足与展望", lambda: ["由于开发周期和项目资料完整度限制，系统仍存在可继续完善的空间，例如界面细节、性能优化、权限粒度、日志审计、自动化测试和部署流程等。后续可结合实际使用反馈持续优化系统功能和用户体验。"]),
    ]
    for marker, generator in generators:
        if marker in key:
            return generator()
    if section.level == 1:
        return [section.purpose or f"本章围绕{section.title}展开说明，重点介绍相关设计依据、实现内容和分析结果。"]
    if "模块" in section.title:
        module_name = section.title.replace("模块", "")
        return [
            f"{module_name}模块是系统的重要组成部分，主要承担与{module_name}相关的数据展示、业务处理和结果反馈功能。实现时需要前端页面、后端接口和数据库表之间保持字段一致。",
            f"该模块的基本流程为：用户进入对应页面，填写或选择业务数据，系统进行合法性校验，后端完成处理后返回结果。若该模块涉及截图，工具会优先根据 screenshots/ 文件名自动插入对应运行效果图。",
            f"【请核对{module_name}模块截图是否与实际页面一致】",
        ]
    return [f"本节主要说明{section.title}相关内容。【请根据项目实际情况补充细节】"]


def _database_design_paragraphs(project: ProjectProfile, table_names: str) -> List[str]:
    if not project.database_tables:
        return [
            "数据库设计围绕系统核心业务对象展开，但当前项目资料中未识别到可用的 database.sql 或表结构文件。",
            "【请补充 database.sql，或在项目资料中加入数据库表结构说明】",
        ]
    table_count = len(project.database_tables)
    field_count = sum(len(table.field_details or table.columns) for table in project.database_tables)
    source_files = sorted({table.source for table in project.database_tables if table.source})
    source_text = "、".join(source_files) if source_files else "database.sql"
    return [
        f"数据库设计依据项目目录中的 SQL 文件自动整理，当前从 {source_text} 中识别到 {table_count} 张数据表、{field_count} 个字段，主要数据表包括{table_names}。",
        "表结构设计以业务实体为中心，字段说明表将列出字段名、字段类型、是否主键、是否允许为空、默认值和字段说明。对于 SQL 中未提供 COMMENT 的字段，工具会根据常见命名规则生成初步说明，并在缺失项报告中提醒人工核对。",
        "【请核对表名、字段类型、主外键关系是否与实际数据库一致】",
        "【请插入数据库 ER 图】",
    ]


def collect_placeholders(sections: Iterable[SectionDraft]) -> List[str]:
    placeholders: List[str] = []
    for section in sections:
        for paragraph in section.paragraphs:
            if "【" in paragraph and "】" in paragraph:
                placeholders.append(paragraph)
        placeholders.extend(collect_placeholders(section.children))
    return placeholders

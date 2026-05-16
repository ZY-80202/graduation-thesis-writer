from pathlib import Path

from thesis_skill.generator.diagram_generator import generate_diagrams
from thesis_skill.models import DatabaseTable, ProjectProfile


def test_generate_diagrams(tmp_path: Path) -> None:
    project = ProjectProfile(
        project_path=str(tmp_path),
        project_name="测试系统",
        technology_stack=["Python", "MySQL"],
        function_modules=["用户管理", "订单管理"],
        database_tables=[DatabaseTable(name="user", columns=["id", "username"])],
    )

    artifacts = generate_diagrams(project, tmp_path / "diagrams")

    assert len(artifacts) == 8
    assert Path(artifacts[0].png_path).exists()
    assert Path(artifacts[0].svg_path).exists()

from pathlib import Path

from PIL import Image

from thesis_skill.parsers.project_parser import parse_project


def test_parse_project_extracts_database_routes_pages_and_screenshots(tmp_path: Path) -> None:
    project = tmp_path / "project"
    backend = project / "source_code" / "backend" / "routes"
    frontend = project / "source_code" / "frontend" / "views"
    screenshots = project / "screenshots"
    backend.mkdir(parents=True)
    frontend.mkdir(parents=True)
    screenshots.mkdir(parents=True)
    (project / "database.sql").write_text(
        """
        CREATE TABLE `user` (
          `id` int NOT NULL AUTO_INCREMENT COMMENT '用户编号',
          `username` varchar(50) NOT NULL COMMENT '用户名',
          `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) COMMENT='用户表';
        """,
        encoding="utf-8",
    )
    (backend / "user_routes.py").write_text(
        '@app.route("/api/login", methods=["POST"])\ndef login():\n    pass\n',
        encoding="utf-8",
    )
    (frontend / "Login.vue").write_text(
        '<template><h1>登录页面</h1></template><script>export default { name: "Login" }</script>',
        encoding="utf-8",
    )
    Image.new("RGB", (80, 50), "white").save(screenshots / "login_page.png")

    profile = parse_project(project, tmp_path / "profiles")

    assert profile.database_tables[0].name == "user"
    assert profile.database_tables[0].field_details[0].is_primary_key is True
    assert profile.database_tables[0].field_details[1].comment == "用户名"
    assert profile.backend_endpoints[0].method == "POST"
    assert profile.backend_endpoints[0].path == "/api/login"
    assert profile.frontend_page_details[0].matched_module == "登录注册"
    assert profile.screenshot_assets[0].inferred_section == "登录"

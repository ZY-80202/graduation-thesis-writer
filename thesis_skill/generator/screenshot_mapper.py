from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class ScreenshotSlot:
    number: int
    caption: str
    kind: str
    filenames: Sequence[str]
    path: Path | None = None
    missing_label: str = ""

    @property
    def figure_caption(self) -> str:
        return f"图 4-{self.number} {self.caption}"

    @property
    def placeholder(self) -> str:
        return f"【请补充：{self.missing_label or self.caption}】"

    @property
    def width_cm(self) -> float:
        return 15.5 if self.kind == "code" else 14.2


IMPLEMENTATION_SLOTS: List[ScreenshotSlot] = [
    ScreenshotSlot(1, "“首页”界面图", "page", ["home.png", "index.png", "首页.png"], missing_label="首页界面截图"),
    ScreenshotSlot(2, "“首页”核心代码图", "code", ["code_home.png", "home_code.png"], missing_label="首页核心代码截图"),
    ScreenshotSlot(3, "“商品展示”界面图", "page", ["products.png", "product_list.png", "goods.png"], missing_label="商品展示页界面截图"),
    ScreenshotSlot(4, "“商品展示”核心代码图", "code", ["code_products.png", "code_product_list.png", "code_goods.png"], missing_label="商品展示核心代码截图"),
    ScreenshotSlot(5, "“商品详情”界面图", "page", ["product_detail.png", "goods_detail.png", "detail.png"], missing_label="商品详情页界面截图"),
    ScreenshotSlot(6, "“商品详情”核心代码图", "code", ["code_product_detail.png", "code_detail.png"], missing_label="商品详情核心代码截图"),
    ScreenshotSlot(7, "“下单结算”界面图", "page", ["orders.png", "checkout.png", "order_submit.png"], missing_label="下单结算页界面截图"),
    ScreenshotSlot(8, "“下单结算”核心代码图", "code", ["code_orders.png", "code_checkout.png"], missing_label="下单结算核心代码截图"),
    ScreenshotSlot(9, "“品牌展示”界面图", "page", ["brands.png", "brand_list.png"], missing_label="品牌展示页界面截图"),
    ScreenshotSlot(10, "“品牌展示”核心代码图", "code", ["code_brands.png", "code_brand_list.png"], missing_label="品牌展示核心代码截图"),
    ScreenshotSlot(11, "“后台商品管理”界面图", "page", ["admin_products.png", "admin_goods.png"], missing_label="后台商品管理页界面截图"),
    ScreenshotSlot(12, "“后台商品管理”核心代码图", "code", ["code_admin_products.png", "code_admin_goods.png"], missing_label="后台商品管理核心代码截图"),
    ScreenshotSlot(13, "“后台品牌管理”界面图", "page", ["admin_brands.png"], missing_label="后台品牌管理页界面截图"),
    ScreenshotSlot(14, "“后台品牌管理”核心代码图", "code", ["code_admin_brands.png"], missing_label="后台品牌管理核心代码截图"),
    ScreenshotSlot(15, "“server.js入口”核心代码图", "code", ["code_server.png", "server.png", "server_js.png"], missing_label="server.js 入口代码截图"),
    ScreenshotSlot(16, "“商品查询接口”核心代码图", "code", ["code_product_query.png", "code_product_api.png"], missing_label="商品查询接口核心代码截图"),
    ScreenshotSlot(17, "“商品新增接口”核心代码图", "code", ["code_product_add.png", "code_product_api.png"], missing_label="商品新增接口核心代码截图"),
    ScreenshotSlot(18, "“商品修改接口”核心代码图", "code", ["code_product_update.png", "code_product_api.png"], missing_label="商品修改接口核心代码截图"),
    ScreenshotSlot(19, "“商品删除接口”核心代码图", "code", ["code_product_delete.png", "code_product_api.png"], missing_label="商品删除接口核心代码截图"),
    ScreenshotSlot(20, "“品牌管理接口”核心代码图", "code", ["code_brand_api.png"], missing_label="品牌管理接口核心代码截图"),
    ScreenshotSlot(21, "“订单提交接口”核心代码图", "code", ["code_order_api.png"], missing_label="订单提交接口核心代码截图"),
    ScreenshotSlot(22, "“订单事务处理”核心代码图", "code", ["code_transaction.png"], missing_label="订单事务处理核心代码截图"),
]


def map_implementation_screenshots(project_path: str | Path) -> List[ScreenshotSlot]:
    root = Path(project_path)
    search_dirs = [root / "screenshots", root / "code_screenshots", root / "source_code", root]
    files = _collect_image_files(search_dirs)
    result: List[ScreenshotSlot] = []
    for slot in IMPLEMENTATION_SLOTS:
        clone = ScreenshotSlot(slot.number, slot.caption, slot.kind, slot.filenames, missing_label=slot.missing_label)
        clone.path = _find_first(files, slot.filenames)
        result.append(clone)
    return result


def missing_screenshot_items(slots: Iterable[ScreenshotSlot]) -> List[str]:
    return [slot.placeholder for slot in slots if slot.path is None]


def _collect_image_files(directories: Sequence[Path]) -> List[Path]:
    suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    seen: set[Path] = set()
    files: List[Path] = []
    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes and path not in seen:
                seen.add(path)
                files.append(path)
    return files


def _find_first(files: Sequence[Path], names: Sequence[str]) -> Path | None:
    lowered = {path.name.lower(): path for path in files}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    stems = {path.stem.lower(): path for path in files}
    for name in names:
        stem = Path(name).stem.lower()
        if stem in stems:
            return stems[stem]
    return None

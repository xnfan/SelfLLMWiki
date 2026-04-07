"""存入路由 — 将查询结果或自定义内容存入 Wiki"""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import DepositRequest, DepositResponse
from ..services.wiki_manager import WikiManager, slugify

router = APIRouter(prefix="/api/deposit", tags=["deposit"])


@router.post("", summary="存入查询结果")
async def deposit_content(body: DepositRequest) -> DepositResponse:
    """将内容存入 Wiki 作为新页面

    如果 slug 为空，则从 title 自动生成。
    """
    wiki = WikiManager()

    # 自动生成 slug
    slug = body.slug or slugify(body.title)
    if not slug:
        return DepositResponse(
            success=False,
            slug="",
            message="无法生成页面 slug，请提供标题或 slug",
        )

    # 检查是否已存在
    if wiki.page_exists(slug):
        # 已存在则追加内容
        existing = wiki.read_page(slug)
        if existing:
            new_content = existing.content + "\n\n---\n\n" + body.content
            wiki.write_page(slug, new_content)
            wiki.append_log("存入（追加）", f"向页面 {slug} 追加了内容", [slug])
            wiki.update_index()
            return DepositResponse(
                success=True,
                slug=slug,
                message=f"内容已追加到已有页面 '{slug}'",
            )

    # 创建新页面
    wiki.write_page(slug, body.content, title=body.title)
    wiki.append_log("存入（新建）", f"创建了页面 {slug}", [slug])
    wiki.update_index()
    return DepositResponse(
        success=True,
        slug=slug,
        message=f"已创建新页面 '{slug}'",
    )

"""健康检查路由 — Wiki 质量检查与报告"""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import LintReport
from ..services.lint_service import LintService

router = APIRouter(prefix="/api/lint", tags=["lint"])

# 缓存最近一次报告
_last_report: LintReport | None = None


@router.post("", summary="运行健康检查")
async def run_lint() -> LintReport:
    """对 Wiki 知识库运行质量检查"""
    global _last_report
    svc = LintService()
    try:
        report = await svc.lint()
        _last_report = report
        return report
    except Exception as e:
        return LintReport(
            issues=[],
            total_pages=0,
            healthy_pages=0,
            timestamp=str(e),
        )


@router.get("/report", summary="获取最近报告")
async def get_lint_report() -> LintReport:
    """获取最近一次健康检查的报告"""
    if _last_report:
        return _last_report
    return LintReport(issues=[], total_pages=0, healthy_pages=0, timestamp="尚未运行检查")

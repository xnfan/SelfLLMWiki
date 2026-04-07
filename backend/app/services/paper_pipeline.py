"""论文处理管线 — PDF 论文 -> 结构化 Wiki 页面"""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path

from ..config import get_config
from ..models.schemas import IngestResponse
from .ingest_service import load_prompt
from .llm import get_llm
from .pdf_converter import convert_pdf_to_markdown
from .wiki_manager import WikiManager, slugify

logger = logging.getLogger(__name__)


class PaperPipeline:
    """论文处理管线：PDF -> Markdown -> LLM 结构化提取 -> Wiki 页面"""

    def __init__(self) -> None:
        self.wiki = WikiManager()

    async def process_paper(
        self,
        pdf_path: Path,
        title: str = "",
    ) -> IngestResponse:
        """处理单篇论文 PDF

        Parameters
        ----------
        pdf_path : Path
            PDF 文件路径
        title : str
            论文标题（可选，如果为空则由 LLM 提取）

        Returns
        -------
        IngestResponse
            处理结果
        """
        try:
            cfg = get_config()

            # 1. PDF -> Markdown
            use_marker = cfg.pdf.converter == "marker"
            md_content = convert_pdf_to_markdown(pdf_path, use_marker=use_marker)

            if md_content.startswith("[错误]"):
                return IngestResponse(
                    success=False,
                    message=md_content,
                )

            # 2. 保存原始 MD 到 raw/papers/
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_filename = f"{timestamp}_{pdf_path.stem}.md"
            self.wiki.save_raw(md_content, "papers", raw_filename)

            # 3. 调用 LLM 用 paper_extract 提示词进行结构化提取
            prompt_template = load_prompt("paper_extract")
            user_prompt = prompt_template.format(paper_content=md_content)

            llm = get_llm()
            provider_cfg = cfg.llm.get_provider()
            extracted = await llm.complete(
                system="",
                user=user_prompt,
                max_tokens=provider_cfg.max_tokens,
                temperature=provider_cfg.temperature,
            )

            # 4. 从提取结果生成 slug 和标题
            # 尝试从 LLM 输出的第一行 H1 标题提取
            paper_title = title
            for line in extracted.splitlines():
                line = line.strip()
                if line.startswith("# ") and not line.startswith("## "):
                    paper_title = line[2:].strip()
                    break

            if not paper_title:
                paper_title = pdf_path.stem

            slug = slugify(f"paper-{paper_title}")

            # 5. 保存到 wiki/pages/
            self.wiki.write_page(slug, extracted, paper_title)

            # 6. 更新索引和日志
            self.wiki.update_index()
            self.wiki.append_log(
                operation="paper_ingest",
                details=f"论文摄入: {paper_title}",
                affected_pages=[slug],
            )

            return IngestResponse(
                success=True,
                pages_created=[slug],
                message=f"论文处理完成: {paper_title}",
            )

        except Exception as exc:
            logger.exception("论文处理失败: %s", pdf_path)
            return IngestResponse(
                success=False,
                message=f"论文处理失败: {exc}",
            )

    async def process_paper_from_bytes(
        self,
        data: bytes,
        filename: str,
    ) -> IngestResponse:
        """从字节数据处理论文（用于文件上传场景）

        Parameters
        ----------
        data : bytes
            PDF 文件的字节内容
        filename : str
            原始文件名

        Returns
        -------
        IngestResponse
            处理结果
        """
        # 先保存到临时文件，然后调用 process_paper
        suffix = Path(filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)

        try:
            # 同时将 PDF 保存到 assets 目录
            cfg = get_config()
            assets_dir = cfg.data.assets_path / "papers"
            assets_dir.mkdir(parents=True, exist_ok=True)
            permanent_path = assets_dir / filename
            permanent_path.write_bytes(data)

            result = await self.process_paper(tmp_path, title=Path(filename).stem)
            return result
        finally:
            # 清理临时文件
            try:
                tmp_path.unlink()
            except OSError:
                pass

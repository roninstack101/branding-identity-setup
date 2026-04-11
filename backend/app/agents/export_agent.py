"""
Agent 10 – Export Agent
Compiles all brand outputs into PDF and DOCX files.
"""
from pathlib import Path

from app.utils.file_export import generate_pdf, generate_docx
from app.schemas.brand_schema import AgentResult


async def run(project_id: str, brand_data: dict) -> AgentResult:
    """Execute the Export Agent – produces PDF and DOCX brand kits."""
    pdf_path = generate_pdf(project_id, brand_data)
    docx_path = generate_docx(project_id, brand_data)
    pdf_name = Path(pdf_path).name
    docx_name = Path(docx_path).name

    data = {
        "pdf_path": pdf_path,
        "docx_path": docx_path,
        "pdf_download_url": f"/exports/{pdf_name}",
        "docx_download_url": f"/exports/{docx_name}",
        "formats_generated": ["pdf", "docx"],
        "sections_included": list(brand_data.keys()),
    }

    explanation = (
        f"Brand kit has been exported in 2 formats: PDF and DOCX. "
        f"PDF saved at: {pdf_path}. "
        f"DOCX saved at: {docx_path}. "
        f"The export includes {len(brand_data)} brand identity sections. "
        f"Both files contain the complete brand identity kit including strategy, "
        f"naming, design direction, content, and guidelines. "
        f"Files are ready for download and distribution."
    )

    return AgentResult(data=data, explanation=explanation)

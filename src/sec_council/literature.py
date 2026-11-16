"""On-demand primary-source discovery; never infer full-text evidence from abstracts."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from .budgets import BudgetExceeded, ResourceBudget

OPENALEX = "https://api.openalex.org"
CROSSREF = "https://api.crossref.org"
PDF_HOSTS = frozenset({
    "arxiv.org", "export.arxiv.org", "zenodo.org", "www.zenodo.org",
    "pmc.ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov", "europepmc.org",
    "www.biorxiv.org", "www.medrxiv.org",
})


@dataclass(frozen=True)
class Paper:
    openalex_id: str
    title: str
    year: int | None
    doi: str | None
    landing_page: str | None
    pdf_url: str | None
    referenced_works: tuple[str, ...]
    metadata_only: bool = True


def _read_bounded(response, limit: int) -> bytes:
    data = response.read(limit + 1)
    if len(data) > limit:
        raise BudgetExceeded("Network response exceeds byte limit")
    return data


def _get_json(url: str, *, allow_hosts: set[str], limit: int = 2_000_000) -> dict:
    host = urllib.parse.urlsplit(url).hostname
    if host not in allow_hosts or not url.startswith("https://"):
        raise PermissionError("Non-allowlisted metadata endpoint")
    req = urllib.request.Request(url, headers={"User-Agent": "SEC-Council/0.1 (research metadata)"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(_read_bounded(response, limit))


def search_openalex(query: str, *, limit: int = 5, network_approved: bool = False,
                    budget: ResourceBudget | None = None) -> list[Paper]:
    if not network_approved:
        raise PermissionError("Online research requires explicit --online")
    budget = budget or ResourceBudget()
    if not query.strip() or not 1 <= limit <= budget.max_initial_papers:
        raise ValueError("Invalid query or paper limit")
    params = urllib.parse.urlencode({"search": query, "per-page": limit})
    data = _get_json(f"{OPENALEX}/works?{params}", allow_hosts={"api.openalex.org"})
    papers = []
    for entry in data.get("results", [])[:limit]:
        loc = entry.get("best_oa_location") or {}
        papers.append(Paper(
            openalex_id=entry.get("id") or "",
            title=entry.get("display_name") or "",
            year=entry.get("publication_year"),
            doi=entry.get("doi"),
            landing_page=loc.get("landing_page_url") or entry.get("doi"),
            pdf_url=loc.get("pdf_url"),
            referenced_works=tuple(entry.get("referenced_works") or ()),
        ))
    return papers


def doi_metadata(doi: str, *, network_approved: bool = False) -> dict:
    if not network_approved:
        raise PermissionError("DOI verification requires explicit --online")
    normalized = doi.strip().removeprefix("https://doi.org/").removeprefix("doi:")
    if not normalized or "/" not in normalized or len(normalized) > 250:
        raise ValueError("Expected a valid DOI identifier")
    url = f"{CROSSREF}/works/{urllib.parse.quote(normalized, safe='/')}"
    data = _get_json(url, allow_hosts={"api.crossref.org"})
    msg = data.get("message", {})
    return {"doi": msg.get("DOI"), "title": (msg.get("title") or [""])[0],
            "publisher": msg.get("publisher"), "type": msg.get("type"),
            "reference_count": msg.get("reference-count", 0),
            "url": msg.get("URL"), "metadata_only": True}


def cited_references(openalex_id: str, *, limit: int = 10,
                     network_approved: bool = False) -> list[str]:
    if not network_approved:
        raise PermissionError("Reference discovery requires explicit --online")
    parsed = urllib.parse.urlsplit(openalex_id)
    if parsed.scheme != "https" or parsed.hostname != "openalex.org":
        raise ValueError("Expected an OpenAlex work URL")
    work_id = parsed.path.strip("/")
    if not work_id.startswith("W") or not work_id[1:].isdigit():
        raise ValueError("Invalid OpenAlex work ID")
    if not 1 <= limit <= 50:
        raise ValueError("Reference limit must be in 1..50")
    data = _get_json(f"{OPENALEX}/works/{work_id}", allow_hosts={"api.openalex.org"})
    return (data.get("referenced_works") or [])[:limit]


def _safe_pdf_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in PDF_HOSTS:
        raise PermissionError("PDF host must be approved and use HTTPS")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise PermissionError("Credentials or custom ports are disallowed")
    for item in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(item[4][0]).is_global:
            raise PermissionError("Non-public network address")


class _PDFRedirectGuard(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _safe_pdf_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_pdf(url: str, target: Path, *, network_approved: bool = False,
                 budget: ResourceBudget | None = None) -> dict:
    """Restricted OA downloader; never auto-download arbitrary publisher URLs."""
    if not network_approved:
        raise PermissionError("PDF download requires explicit --online")
    _safe_pdf_url(url)
    budget = budget or ResourceBudget()
    target = Path(target)
    if target.exists():
        raise FileExistsError("Refusing to overwrite existing PDF")
    opener = urllib.request.build_opener(_PDFRedirectGuard())
    req = urllib.request.Request(url, headers={"User-Agent": "SEC-Council/0.1"})
    with opener.open(req, timeout=20) as response:
        body = _read_bounded(response, budget.max_pdf_bytes)
    if not body.lstrip()[:5] == b"%PDF-":
        raise ValueError("Response is not a PDF document")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation after validating bytes; no partial file is published.
    with target.open("xb") as stream:
        stream.write(body)
    return {"path": str(target), "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(), "source": url}


def pdf_text_pages(path: Path, *, max_pages: int = 12) -> list[dict]:
    """Optional local extraction, bounded by page count; no OCR or unsupported claims."""
    if not 1 <= max_pages <= 50:
        raise ValueError("Page count must be in 1..50")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install the PDF extra: pip install '.[pdf]'") from exc
    reader = PdfReader(str(path))
    return [{"page": i + 1, "text": reader.pages[i].extract_text() or ""}
            for i in range(min(len(reader.pages), max_pages))]

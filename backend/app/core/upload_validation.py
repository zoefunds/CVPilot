"""
Magic-byte sniffing and size caps for user uploads.

Trust the bytes, not the Content-Type header the client sent. Used by
the application submission endpoint to reject anything that is not a
PDF, DOCX, or plain text resume/cover letter.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.exceptions import ValidationError

# Hard caps. Per-file cap is generous for a CV; total request cap stops
# someone shipping two near-max files.
MAX_FILE_BYTES = 4 * 1024 * 1024       # 4 MiB
MAX_TOTAL_BYTES = 6 * 1024 * 1024      # 6 MiB combined

_PDF_MAGIC = b"%PDF-"
_DOCX_MAGIC = b"PK\x03\x04"  # zip container; DOCX is a zip


@dataclass(frozen=True)
class SniffResult:
    kind: str          # 'pdf' | 'docx' | 'text'
    extension: str     # '.pdf' | '.docx' | '.txt'


def _looks_like_text(data: bytes) -> bool:
    if not data:
        return False
    sample = data[:2048]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        try:
            sample.decode("latin-1")
            return True
        except UnicodeDecodeError:
            return False


def sniff(data: bytes, *, field: str) -> SniffResult:
    """Identify the file by magic bytes. Raises ValidationError if the
    payload is empty, oversized, or not a supported type."""
    if not data:
        raise ValidationError(f"{field}: file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ValidationError(
            f"{field}: file exceeds {MAX_FILE_BYTES // (1024 * 1024)} MiB limit."
        )
    if data.startswith(_PDF_MAGIC):
        return SniffResult(kind="pdf", extension=".pdf")
    if data.startswith(_DOCX_MAGIC):
        # Could be any zip; we accept it as DOCX. python-docx will reject
        # garbage downstream during parsing.
        return SniffResult(kind="docx", extension=".docx")
    if _looks_like_text(data):
        return SniffResult(kind="text", extension=".txt")
    raise ValidationError(
        f"{field}: unsupported file type. Allowed: PDF, DOCX, or plain text."
    )


def assert_total_size(*chunks: bytes) -> None:
    total = sum(len(c) for c in chunks)
    if total > MAX_TOTAL_BYTES:
        raise ValidationError(
            f"Combined upload size exceeds {MAX_TOTAL_BYTES // (1024 * 1024)} MiB."
        )

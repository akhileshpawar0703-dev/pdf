#!/usr/bin/env python3
"""A lightweight PDF editing CLI with essential Adobe-like operations."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

PdfReader = None
PdfWriter = None


def _ensure_pdf_backend() -> None:
    global PdfReader, PdfWriter
    if PdfReader is not None and PdfWriter is not None:
        return
    try:
        from pypdf import PdfReader as _PdfReader, PdfWriter as _PdfWriter
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: install with `pip install -r requirements.txt` to enable PDF operations."
        ) from exc
    PdfReader, PdfWriter = _PdfReader, _PdfWriter


@dataclass(frozen=True)
class PageSelection:
    """Represents zero-based page indexes selected from a user expression."""

    indexes: List[int]


def parse_page_selection(selection: str, page_count: int) -> PageSelection:
    """Parse page expressions like '1,3,5-7,10-' into zero-based indexes."""
    if not selection.strip():
        raise ValueError("Page selection cannot be empty.")

    indexes: list[int] = []
    tokens = [token.strip() for token in selection.split(",") if token.strip()]

    for token in tokens:
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text) if start_text else 1
            end = int(end_text) if end_text else page_count
            if start < 1 or end < 1:
                raise ValueError(f"Page ranges must start at 1: '{token}'")
            if end < start:
                raise ValueError(f"Invalid page range '{token}' (end before start).")
            indexes.extend(range(start - 1, end))
        else:
            number = int(token)
            if number < 1:
                raise ValueError(f"Page numbers must start at 1: '{token}'")
            indexes.append(number - 1)

    unique_indexes = []
    seen = set()
    for idx in indexes:
        if idx >= page_count:
            raise ValueError(f"Page {idx + 1} is out of bounds (PDF has {page_count} pages).")
        if idx not in seen:
            seen.add(idx)
            unique_indexes.append(idx)

    if not unique_indexes:
        raise ValueError("Selection produced no pages.")

    return PageSelection(indexes=unique_indexes)


def write_output(writer: PdfWriter, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        writer.write(f)


def merge_pdfs(inputs: Iterable[Path], output: Path) -> None:
    _ensure_pdf_backend()
    writer = PdfWriter()
    for input_path in inputs:
        reader = PdfReader(str(input_path))
        for page in reader.pages:
            writer.add_page(page)
    write_output(writer, output)


def split_pdf(input_path: Path, output_dir: Path, prefix: str = "page") -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        with (output_dir / f"{prefix}_{idx:03}.pdf").open("wb") as f:
            writer.write(f)


def extract_pages(input_path: Path, output_path: Path, selection: str) -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    chosen = parse_page_selection(selection, len(reader.pages))
    writer = PdfWriter()
    for idx in chosen.indexes:
        writer.add_page(reader.pages[idx])
    write_output(writer, output_path)


def remove_pages(input_path: Path, output_path: Path, selection: str) -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    to_remove = set(parse_page_selection(selection, len(reader.pages)).indexes)

    writer = PdfWriter()
    for idx, page in enumerate(reader.pages):
        if idx not in to_remove:
            writer.add_page(page)
    write_output(writer, output_path)


def rotate_pages(input_path: Path, output_path: Path, selection: str, angle: int) -> None:
    _ensure_pdf_backend()
    if angle % 90 != 0:
        raise ValueError("Rotation angle must be a multiple of 90.")

    reader = PdfReader(str(input_path))
    to_rotate = set(parse_page_selection(selection, len(reader.pages)).indexes)

    writer = PdfWriter()
    for idx, page in enumerate(reader.pages):
        if idx in to_rotate:
            page.rotate(angle)
        writer.add_page(page)
    write_output(writer, output_path)


def reorder_pages(input_path: Path, output_path: Path, selection: str) -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    new_order = parse_page_selection(selection, len(reader.pages)).indexes

    writer = PdfWriter()
    for idx in new_order:
        writer.add_page(reader.pages[idx])
    write_output(writer, output_path)


def encrypt_pdf(input_path: Path, output_path: Path, password: str) -> None:
    _ensure_pdf_backend()
    if not password:
        raise ValueError("Password cannot be empty.")
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    write_output(writer, output_path)


def decrypt_pdf(input_path: Path, output_path: Path, password: str) -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    if not reader.is_encrypted:
        raise ValueError("Input PDF is not encrypted.")

    result = reader.decrypt(password)
    if result == 0:
        raise ValueError("Wrong password or unsupported encryption.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    write_output(writer, output_path)


def show_metadata(input_path: Path) -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    metadata = reader.metadata or {}
    if not metadata:
        print("No metadata found.")
        return
    for key, value in metadata.items():
        print(f"{key}: {value}")


def set_metadata(input_path: Path, output_path: Path, entries: list[str]) -> None:
    _ensure_pdf_backend()
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    metadata: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"Metadata entry must be KEY=VALUE, got '{entry}'.")
        key, value = entry.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("Metadata keys cannot be empty.")
        if not key.startswith("/"):
            key = f"/{key}"
        metadata[key] = value

    writer.add_metadata(metadata)
    write_output(writer, output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-editor",
        description="Essential PDF editor CLI: merge, split, rotate, extract, reorder, encrypt, metadata.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    merge_cmd = sub.add_parser("merge", help="Merge multiple PDFs into one output file.")
    merge_cmd.add_argument("inputs", nargs="+", type=Path, help="Input PDF files.")
    merge_cmd.add_argument("-o", "--output", required=True, type=Path, help="Merged output PDF path.")

    split_cmd = sub.add_parser("split", help="Split a PDF into one file per page.")
    split_cmd.add_argument("input", type=Path)
    split_cmd.add_argument("-d", "--output-dir", required=True, type=Path)
    split_cmd.add_argument("--prefix", default="page", help="Output file prefix.")

    extract_cmd = sub.add_parser("extract", help="Extract selected pages into a new PDF.")
    extract_cmd.add_argument("input", type=Path)
    extract_cmd.add_argument("-p", "--pages", required=True, help="Page selection, e.g. 1,3-5,8-")
    extract_cmd.add_argument("-o", "--output", required=True, type=Path)

    delete_cmd = sub.add_parser("delete", help="Delete selected pages from a PDF.")
    delete_cmd.add_argument("input", type=Path)
    delete_cmd.add_argument("-p", "--pages", required=True)
    delete_cmd.add_argument("-o", "--output", required=True, type=Path)

    rotate_cmd = sub.add_parser("rotate", help="Rotate selected pages.")
    rotate_cmd.add_argument("input", type=Path)
    rotate_cmd.add_argument("-p", "--pages", required=True)
    rotate_cmd.add_argument("-a", "--angle", type=int, required=True, help="Angle in degrees (multiple of 90).")
    rotate_cmd.add_argument("-o", "--output", required=True, type=Path)

    reorder_cmd = sub.add_parser("reorder", help="Create a new PDF by page order expression.")
    reorder_cmd.add_argument("input", type=Path)
    reorder_cmd.add_argument("-p", "--pages", required=True, help="Exact new page order, e.g. 3,1,2")
    reorder_cmd.add_argument("-o", "--output", required=True, type=Path)

    encrypt_cmd = sub.add_parser("encrypt", help="Encrypt PDF with a password.")
    encrypt_cmd.add_argument("input", type=Path)
    encrypt_cmd.add_argument("-s", "--password", required=True)
    encrypt_cmd.add_argument("-o", "--output", required=True, type=Path)

    decrypt_cmd = sub.add_parser("decrypt", help="Decrypt password-protected PDF.")
    decrypt_cmd.add_argument("input", type=Path)
    decrypt_cmd.add_argument("-s", "--password", required=True)
    decrypt_cmd.add_argument("-o", "--output", required=True, type=Path)

    metadata_show_cmd = sub.add_parser("metadata-show", help="Print metadata.")
    metadata_show_cmd.add_argument("input", type=Path)

    metadata_set_cmd = sub.add_parser("metadata-set", help="Set metadata fields.")
    metadata_set_cmd.add_argument("input", type=Path)
    metadata_set_cmd.add_argument("-m", "--meta", action="append", required=True, help="Metadata KEY=VALUE (repeatable).")
    metadata_set_cmd.add_argument("-o", "--output", required=True, type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "merge":
            merge_pdfs(args.inputs, args.output)
        elif args.command == "split":
            split_pdf(args.input, args.output_dir, args.prefix)
        elif args.command == "extract":
            extract_pages(args.input, args.output, args.pages)
        elif args.command == "delete":
            remove_pages(args.input, args.output, args.pages)
        elif args.command == "rotate":
            rotate_pages(args.input, args.output, args.pages, args.angle)
        elif args.command == "reorder":
            reorder_pages(args.input, args.output, args.pages)
        elif args.command == "encrypt":
            encrypt_pdf(args.input, args.output, args.password)
        elif args.command == "decrypt":
            decrypt_pdf(args.input, args.output, args.password)
        elif args.command == "metadata-show":
            show_metadata(args.input)
        elif args.command == "metadata-set":
            set_metadata(args.input, args.output, args.meta)
        else:
            raise RuntimeError(f"Unhandled command: {args.command}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

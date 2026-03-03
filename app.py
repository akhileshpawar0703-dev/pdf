from __future__ import annotations

import cgi
import json
import os
import re
import threading
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "4173"))


@dataclass
class StoredPDF:
    name: str
    content: bytes


PDF_STORE: dict[str, StoredPDF] = {}
STORE_LOCK = threading.Lock()


class PDFReaderHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/":
            return self._serve_file(ROOT / "index.html", "text/html; charset=utf-8")

        if self.path.startswith("/static/"):
            safe_name = self.path.removeprefix("/static/")
            if ".." in safe_name:
                return self._json_error(HTTPStatus.BAD_REQUEST, "Invalid path")
            file_path = STATIC_DIR / safe_name
            if not file_path.exists() or not file_path.is_file():
                return self._json_error(HTTPStatus.NOT_FOUND, "File not found")
            mime = "text/plain; charset=utf-8"
            if safe_name.endswith(".css"):
                mime = "text/css; charset=utf-8"
            elif safe_name.endswith(".js"):
                mime = "application/javascript; charset=utf-8"
            return self._serve_file(file_path, mime)

        pdf_match = re.fullmatch(r"/pdf/([a-f0-9\-]+)", self.path)
        if pdf_match:
            file_id = pdf_match.group(1)
            with STORE_LOCK:
                stored = PDF_STORE.get(file_id)
            if stored is None:
                return self._json_error(HTTPStatus.NOT_FOUND, "PDF not found")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'inline; filename="{stored.name}"')
            self.send_header("Content-Length", str(len(stored.content)))
            self.end_headers()
            self.wfile.write(stored.content)
            return

        return self._json_error(HTTPStatus.NOT_FOUND, "Route not found")

    def do_POST(self) -> None:
        if self.path != "/upload":
            return self._json_error(HTTPStatus.NOT_FOUND, "Route not found")

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            },
        )

        pdf_file = form["pdf"] if "pdf" in form else None
        if pdf_file is None or not getattr(pdf_file, "file", None):
            return self._json_error(HTTPStatus.BAD_REQUEST, "Missing PDF file")

        raw = pdf_file.file.read()
        if not raw.startswith(b"%PDF"):
            return self._json_error(HTTPStatus.BAD_REQUEST, "Uploaded file is not a valid PDF")

        file_id = str(uuid.uuid4())
        filename = os.path.basename(getattr(pdf_file, "filename", "document.pdf")) or "document.pdf"
        with STORE_LOCK:
            PDF_STORE[file_id] = StoredPDF(name=filename, content=raw)

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        payload = {"id": file_id, "name": filename, "url": f"/pdf/{file_id}"}
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        return super().log_message(format, *args)

    def _serve_file(self, file_path: Path, content_type: str) -> None:
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status: HTTPStatus, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PDFReaderHandler)
    print(f"PDF reader running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()

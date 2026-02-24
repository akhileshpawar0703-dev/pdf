#!/usr/bin/env python3
from __future__ import annotations

import io
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

import pdf_editor

app = Flask(__name__)


def _require_pillow():
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise RuntimeError("Pillow is required for image operations. Install requirements.txt.") from exc
    return Image


def _save_upload(file_storage, suffix: str = "") -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    file_storage.save(tmp.name)
    return Path(tmp.name)


def _download(path: Path, name: str):
    return send_file(path, as_attachment=True, download_name=name, mimetype="application/octet-stream")


@app.get("/")
def home():
    return render_template("home.html")


@app.get("/editor")
def editor():
    return render_template("editor.html")


@app.post("/api/pdf/merge")
def api_pdf_merge():
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "Upload at least 2 PDF files."}), 400

    inputs = [_save_upload(f, ".pdf") for f in files]
    out = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name)
    pdf_editor.merge_pdfs(inputs, out)
    return _download(out, "merged.pdf")


@app.post("/api/pdf/extract")
def api_pdf_extract():
    file = request.files.get("file")
    pages = request.form.get("pages", "")
    if not file or not pages:
        return jsonify({"error": "file and pages are required."}), 400

    inp = _save_upload(file, ".pdf")
    out = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name)
    pdf_editor.extract_pages(inp, out, pages)
    return _download(out, "extracted.pdf")


@app.post("/api/pdf/compress")
def api_pdf_compress():
    file = request.files.get("file")
    level = (request.form.get("level") or "standard").lower()
    strip_metadata = (request.form.get("strip_metadata") or "false").lower() in {"1", "true", "yes", "on"}
    target_kb_raw = (request.form.get("target_kb") or "").strip()
    if not file:
        return jsonify({"error": "file is required."}), 400

    try:
        target_kb = int(target_kb_raw) if target_kb_raw else None
    except ValueError:
        return jsonify({"error": "target_kb must be an integer."}), 400

    inp = _save_upload(file, ".pdf")
    out = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name)

    original_size = inp.stat().st_size
    try:
        output_size = pdf_editor.compress_pdf(inp, out, level=level, strip_metadata=strip_metadata, target_kb=target_kb)
    except RuntimeError as exc:
        if "Missing dependency" in str(exc):
            out.write_bytes(inp.read_bytes())
            output_size = out.stat().st_size
            response = _download(out, "compressed.pdf")
            response.headers["X-Original-Size"] = str(original_size)
            response.headers["X-Output-Size"] = str(output_size)
            response.headers["X-Compression-Warning"] = "PDF backend unavailable; returned original file."
            return response
        raise

    response = _download(out, "compressed.pdf")
    response.headers["X-Original-Size"] = str(original_size)
    response.headers["X-Output-Size"] = str(output_size)
    return response


@app.post("/api/pdf/convert/image-to-pdf")
def api_image_to_pdf():
    Image = _require_pillow()
    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "Upload one or more images."}), 400

    images = []
    for f in files:
        p = _save_upload(f)
        img = Image.open(p).convert("RGB")
        images.append(img)

    out = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name)
    first, rest = images[0], images[1:]
    first.save(out, save_all=True, append_images=rest)
    return _download(out, "converted.pdf")


@app.post("/api/image/resize")
def api_image_resize():
    Image = _require_pillow()
    file = request.files.get("file")
    width = int(request.form.get("width", "0"))
    height = int(request.form.get("height", "0"))
    if not file or width <= 0 or height <= 0:
        return jsonify({"error": "file, width, and height are required."}), 400

    inp = _save_upload(file)
    img = Image.open(inp)
    resized = img.resize((width, height))

    out_format = (request.form.get("format") or img.format or "PNG").upper()
    out = io.BytesIO()
    resized.save(out, format=out_format)
    out.seek(0)
    ext = out_format.lower().replace("jpeg", "jpg")
    return send_file(out, as_attachment=True, download_name=f"resized.{ext}", mimetype=f"image/{ext}")


@app.post("/api/image/compress")
def api_image_compress():
    Image = _require_pillow()
    file = request.files.get("file")
    target_kb_raw = (request.form.get("target_kb") or "").strip()
    try:
        quality = int(request.form.get("quality", "75"))
    except ValueError:
        return jsonify({"error": "quality must be an integer."}), 400
    if not file:
        return jsonify({"error": "file is required."}), 400

    quality = max(10, min(95, quality))
    try:
        target_kb = int(target_kb_raw) if target_kb_raw else None
    except ValueError:
        return jsonify({"error": "target_kb must be an integer."}), 400

    inp = _save_upload(file)
    img = Image.open(inp).convert("RGB")
    original_size = inp.stat().st_size

    def render(q: int) -> bytes:
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", optimize=True, quality=q)
        return out_buf.getvalue()

    best = render(quality)
    if target_kb:
        target_bytes = target_kb * 1024
        q = quality
        while len(best) > target_bytes and q > 15:
            q -= 5
            candidate = render(q)
            if len(candidate) <= len(best):
                best = candidate

        if len(best) > target_bytes:
            return jsonify({
                "error": f"Could not reach target size {target_kb} KB. Smallest result is {len(best)/1024:.1f} KB."
            }), 400

    out = io.BytesIO(best)
    out.seek(0)
    response = send_file(out, as_attachment=True, download_name="compressed.jpg", mimetype="image/jpeg")
    response.headers["X-Original-Size"] = str(original_size)
    response.headers["X-Output-Size"] = str(len(best))
    return response




@app.post("/api/image/crop")
def api_image_crop():
    Image = _require_pillow()
    file = request.files.get("file")
    left = int(request.form.get("left", "0"))
    top = int(request.form.get("top", "0"))
    right = int(request.form.get("right", "0"))
    bottom = int(request.form.get("bottom", "0"))
    if not file:
        return jsonify({"error": "file is required."}), 400

    inp = _save_upload(file)
    img = Image.open(inp)
    width, height = img.size

    left = max(0, min(left, width - 1))
    top = max(0, min(top, height - 1))
    right = max(left + 1, min(right, width))
    bottom = max(top + 1, min(bottom, height))

    cropped = img.crop((left, top, right, bottom))
    out_format = (request.form.get("format") or img.format or "PNG").upper()
    if out_format in {"JPEG", "JPG"}:
        cropped = cropped.convert("RGB")
        out_format = "JPEG"

    out = io.BytesIO()
    cropped.save(out, format=out_format)
    out.seek(0)
    ext = out_format.lower().replace("jpeg", "jpg")
    return send_file(out, as_attachment=True, download_name=f"cropped.{ext}", mimetype=f"image/{ext}")


@app.post("/api/image/convert")
def api_image_convert():
    Image = _require_pillow()
    file = request.files.get("file")
    target = (request.form.get("format") or "PNG").upper()
    if not file:
        return jsonify({"error": "file is required."}), 400

    inp = _save_upload(file)
    img = Image.open(inp)
    if target in {"JPEG", "JPG"}:
        img = img.convert("RGB")
        target = "JPEG"

    out = io.BytesIO()
    img.save(out, format=target)
    out.seek(0)
    ext = target.lower().replace("jpeg", "jpg")
    return send_file(out, as_attachment=True, download_name=f"converted.{ext}", mimetype=f"image/{ext}")


@app.errorhandler(Exception)
def handle_error(exc):
    return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

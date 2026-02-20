# StudioPDF: Modern PDF + Image Editor (UI + API + CLI)

StudioPDF is a modern editing toolkit that combines:
- Beautiful web UI
- REST API for automation/integration
- CLI for scripting

## Core Features

### PDF features
- Merge PDFs
- Extract specific pages (`1,3-5,8-` style)
- Delete pages
- Rotate pages
- Reorder pages
- Encrypt/decrypt
- Metadata show/set
- Basic PDF compression with configurable level (low/standard/high) and optional metadata stripping
- Convert images to PDF

### Image features
- Resize
- Compress (quality-based JPEG optimization)
- Convert formats (PNG/JPEG/WEBP/BMP)
- Crop images with custom bounds (left/top/right/bottom)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open Home: `http://localhost:8000`

Editor: `http://localhost:8000/editor`

## API Endpoints

- `POST /api/pdf/merge`
- `POST /api/pdf/extract`
- `POST /api/pdf/compress` (supports `level=low|standard|high` and optional `strip_metadata=true`)
- `POST /api/pdf/convert/image-to-pdf`
- `POST /api/image/resize`
- `POST /api/image/compress`
- `POST /api/image/convert`
- `POST /api/image/crop`

## CLI

The existing CLI is still available:

```bash
python pdf_editor.py --help
```


## UI Flow

- The editor now uses a split layout: **left side panel buttons + expandable toolbars/settings**, **right side live preview**.
- Click panel buttons (Settings / PDF Toolbar / Image Toolbar) to show that panel; tool sections inside each toolbar expand natively to reveal options.
- New UI enhancement: a **Recent Actions** panel logs started/completed/failed operations with timestamps for quick feedback.
- Added **Find a tool** search and **Expand all / Collapse all** controls in toolbars for faster navigation in larger tool sets.
- The right-side preview updates from selected files (image preview, embedded PDF preview, or multi-file list).
- New UX feature: selectable accent theme (White/Blue/Violet/Emerald), appearance mode (System/Light/Dark), optional remembered panel, and dedicated **Use White Theme** / **Use Dark Mode** buttons in editor settings.
- Home page includes visual illustrations, animated decorative elements, and interactive feature cards for a more polished look.
- UI uses a clean light (white-first) visual theme for better readability.

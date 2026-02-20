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
- Basic PDF compression (stream rewrite + object deduplication when supported)
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
- `POST /api/pdf/compress`
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

- The editor now uses a split layout: **left side accordion toolbar + settings**, **right side live preview**.
- Tools are listed one-by-one and use native expandable sections; clicking a tool title expands its settings + action button.
- The right-side preview updates from selected files (image preview, embedded PDF preview, or multi-file list).
- New UX feature: selectable accent theme (White/Blue/Violet/Emerald), optional remembered workspace, and a dedicated **Use White Theme** button in editor settings.
- Home page includes visual illustrations, animated decorative elements, and interactive feature cards for a more polished look.
- UI uses a clean light (white-first) visual theme for better readability.

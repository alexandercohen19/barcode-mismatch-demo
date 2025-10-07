# Barcode/Label Mismatch Detector — Mini Prototype

This mini-build demonstrates a **warehouse inventory accuracy** use case: flagging when the **visible barcode** on a shelf/pallet **does not match** the **expected** code for that location.

## Why this matters (Business Process Need)
- Mislabeled locations cause **mis-picks**, rework, and cycle count discrepancies.
- A simple image check can catch **label/slotting errors** early.

## How the prototype works (Tool Choice & Rationale)
- **Computer Vision**: draw a bounding box and overlay PASS/FAIL.
- **Barcode decoding**: uses `pyzbar` if installed; otherwise, a **fallback** parses the synthetic image filename so you can demo without extra libs.
- Synthetic data generated with **Pillow**; no photos required.

## What's included
```
cv-mismatch-demo/
  images_raw/         # synthetic demo images (PASS + FAIL)
  outputs/            # annotated results (created at runtime)
  expected.csv        # mapping of location -> expected barcode
  manifest.json       # convenience metadata for generated images
  app.py              # Streamlit UI (single + batch mode)
  cv_core.py          # drawing utilities
  requirements.txt    # pip packages
  README.md           # this file
```

## Quickstart (local)
```bash
cd cv-mismatch-demo
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
- Upload one of the files from `images_raw/` or run **Batch mode**.
- The app shows **Detected vs Expected** and an annotated image with **PASS/FAIL**.

> Tip: If you want **real barcode decoding**, install `pyzbar` (`pip install pyzbar`) and platform dependencies (ZBar). Otherwise, the demo still works via filename fallback.

## Data & Demo
- `expected.csv` lists expected barcodes for each location (A-01-01 .. A-03-05).
- `images_raw/` includes ~15 synthetic images.
- About 25% are intentional **FAIL** examples.

## Rubric mapping (for your submission)
- **Business Process Need (25 pts)**: Inventory accuracy & mislabel detection.
- **Tool Choice Rationale (25 pts)**: CV + barcode decoding is the most direct and demo-friendly approach.
- **Prototype Demo (50 pts)**: Screenshots of upload, PASS, FAIL, and batch table. (You can also export annotated images from `outputs/`.)

## Optional Enhancements
- Add **OpenCV** to improve preprocessing (deskew, threshold).
- Add **Tesseract OCR** to read human text if barcode missing.
- Train a tiny detector (YOLOv8n) to auto-locate the label region.

---

Created for your MBA mini-build. Good luck!

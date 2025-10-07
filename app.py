import os
import re
import time
import csv
import json
import io
import base64
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

# Optional: barcode decoding (if installed)
PYZBAR_AVAILABLE = False
try:
    from pyzbar.pyzbar import decode as zbar_decode
    PYZBAR_AVAILABLE = True
except Exception as e:
    PYZBAR_AVAILABLE = False

# Local utils
from cv_core import draw_bbox

st.set_page_config(page_title="Barcode/Label Mismatch Detector", page_icon="📦", layout="wide")
st.title("📦 Barcode/Label Mismatch Detector — Mini Prototype")

st.markdown("""
This demo flags when the **detected barcode** on a shelf label **does not match** the **expected** code for that location.
- **Mode A:** Try real decoding via `pyzbar` if installed
- **Mode B (fallback):** Parse the barcode value from the uploaded image **filename** (synthetic dataset embeds the code)
""")

# Load expected reference
def load_expected(path: Path):
    table = {}
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            table[row["location_id"]] = row["expected_barcode"]
    return table

# Parse location and "detected" code from filename like "A-01-01__012345678905.png"
def parse_from_filename(name: str):
    # captures "A-01-01" and "012345678905"
    m = re.match(r"([A-Z]-\d{2}-\d{2})__([0-9A-Za-z]+)", name)
    if not m:
        return None, None
    return m.group(1), m.group(2)

def try_decode_barcode(pil_img):
    """Attempt real barcode decode via pyzbar. Returns (code, bbox) or (None, None)"""
    if not PYZBAR_AVAILABLE:
        return None, None
    try:
        results = zbar_decode(pil_img)
        if not results:
            return None, None
        # choose the longest result (most reliable)
        best = max(results, key=lambda r: len(r.data or b""))
        code = best.data.decode("utf-8")
        x, y, w, h = best.rect.left, best.rect.top, best.rect.width, best.rect.height
        bbox = (x, y, x+w, y+h)
        return code, bbox
    except Exception as e:
        return None, None

# Sidebar controls
demo_dir = Path("images_raw")
expected_csv = Path("expected.csv")
expected = load_expected(expected_csv)

st.sidebar.header("Options")
mode = st.sidebar.radio("Detection mode", ["Auto (decode then fallback)", "Filename only (simulate)"])
batch = st.sidebar.checkbox("Batch folder mode", value=False)

if not batch:
    up = st.file_uploader("Upload one image (use the provided synthetic images for easiest demo)", type=["png","jpg","jpeg"])
    if up:
        pil = Image.open(up).convert("RGB")
        name = up.name
        st.image(pil, caption=f"Uploaded: {name}", use_column_width=True)

        # choose barcode code
        detected_code, bbox = (None, None)
        if mode.startswith("Auto"):
            detected_code, bbox = try_decode_barcode(pil)
        if detected_code is None:
            # fallback to filename parsing
            loc_id, code_from_name = parse_from_filename(name)
            detected_code = code_from_name
            # best-effort bbox: draw a mid rectangle
            W, H = pil.size
            bbox = (int(W*0.2), int(H*0.45), int(W*0.8), int(H*0.65))

        # Choose location
        loc_id_infer, code_from_name = parse_from_filename(name)
        loc_id = st.text_input("Location (auto-filled from filename if present)", value=loc_id_infer or "")

        expected_code = expected.get(loc_id, None)
        if expected_code is None:
            st.warning("No expected barcode for this location in expected.csv")
        else:
            result = "PASS" if (detected_code == expected_code) else "FAIL"
            st.subheader(f"Result: {result}")
            st.write(f"**Detected:** `{detected_code}`  |  **Expected:** `{expected_code}`  |  **Location:** `{loc_id}`")

            # Render annotated image
            from cv_core import draw_bbox
            # Save upload to temp to annotate
            tmp_path = Path("outputs") / ("_tmp_" + name)
            Path("outputs").mkdir(exist_ok=True)
            pil.save(tmp_path)
            out_path = draw_bbox(str(tmp_path), bbox, result)
            st.image(Image.open(out_path), caption=f"Annotated ({result})", use_column_width=True)

else:
    st.info("Batch mode processes every image in /images_raw and summarizes results.")
    if st.button("Run batch"):
        rows = []
        for img_path in sorted(demo_dir.glob("*.png")):
            pil = Image.open(img_path).convert("RGB")
            name = img_path.name
            loc_id, code_from_name = parse_from_filename(name)

            detected_code, bbox = (None, None)
            if mode.startswith("Auto"):
                detected_code, bbox = try_decode_barcode(pil)
            if detected_code is None:
                detected_code = code_from_name
                W,H = pil.size
                bbox = (int(W*0.2), int(H*0.45), int(W*0.8), int(H*0.65))

            expected_code = expected.get(loc_id, None)
            result = "UNKNOWN"
            if expected_code is not None and detected_code is not None:
                result = "PASS" if (detected_code == expected_code) else "FAIL"

            from cv_core import draw_bbox
            out_dir = Path("outputs")
            out_dir.mkdir(exist_ok=True)
            annotated_path = draw_bbox(str(img_path), bbox, result, save_path=str(out_dir / f"{name.replace('.png','')}__{result}.png"))
            rows.append((name, loc_id, detected_code, expected_code, result, annotated_path))

        # Show table and quick metrics
        import pandas as pd
        df = pd.DataFrame(rows, columns=["filename","location","detected","expected","result","annotated_path"])
        st.dataframe(df[["filename","location","detected","expected","result"]])
        total = len(df)
        fails = (df["result"]=="FAIL").sum()
        passes = (df["result"]=="PASS").sum()
        st.metric("Total processed", total)
        st.metric("PASS", passes)
        st.metric("FAIL", fails)

        # Provide download of outputs as a zip
        mem_zip = io.BytesIO()
        import zipfile
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in Path("outputs").glob("*.png"):
                zf.write(p, arcname=p.name)
        st.download_button("Download annotated results (zip)", data=mem_zip.getvalue(), file_name="annotated_results.zip", mime="application/zip")

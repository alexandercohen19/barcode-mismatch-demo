python
import os
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

def draw_bbox(image_path: str, bbox: Tuple[int,int,int,int], result: str, save_path: Optional[str]=None):
    """Draw a rectangle and PASS/FAIL banner on an image."""
    img = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(img)
    x1,y1,x2,y2 = bbox
    color = (0,160,0) if result.upper()=="PASS" else (200,0,0)
    d.rectangle([x1,y1,x2,y2], outline=color, width=4)

    banner_h = 36
    d.rectangle([x1, y1-banner_h-4, x1+160, y1-4], fill=color)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except:
        font = ImageFont.load_default()
    d.text((x1+8, y1-banner_h-2), result.upper(), fill=(255,255,255), font=font)

    if save_path is None:
        root, ext = os.path.splitext(image_path)
        save_path = f"{root}__{result.upper()}.png"
    img.save(save_path)
    return save_path

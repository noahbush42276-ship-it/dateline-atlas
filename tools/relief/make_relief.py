"""Higher-resolution globe texture for Dateline Atlas, with optional extra elevation shading.

Runs in GitHub Actions (it downloads ~1 GB of public-domain map data):
  - Natural Earth "Cross Blended Hypso with Shaded Relief, Water, Drainages and Ocean Bottom"
    (HYP_HR_SR_OB_DR, 21600 x 10800): the same style as the app's current 4k texture, 5x the detail.
  - NOAA ETOPO elevation (1 arc-minute) for an extra, vertically exaggerated hillshade that makes
    mountain ranges stand out in proportion to their real height.

python make_relief.py preview  <out-dir>          -> side-by-side previews (current vs sharper vs sharper + relief)
python make_relief.py tiles    <out-dir> <mode>   -> 2k/4k base + 16384x8192 detail tiles (mode: plain | relief)
"""
import io, json, math, os, sys, zipfile, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
CACHE = os.environ.get("RELIEF_CACHE", "/tmp/relief-cache")
os.makedirs(CACHE, exist_ok=True)

NE_URLS = ["https://naciscdn.org/naturalearth/10m/raster/HYP_HR_SR_OB_DR.zip"]
ETOPO_URLS = [
    "https://www.ngdc.noaa.gov/thredds/fileServer/global/ETOPO2022/60s/60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif",
    "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/georeferenced_tiff/ETOPO1_Ice_g_geotiff.zip",
]


def fetch(urls, name):
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        return path
    last = None
    for u in urls:
        try:
            print("downloading", u, flush=True)
            req = urllib.request.Request(u, headers={"User-Agent": "dateline-atlas-relief/1.0"})
            with urllib.request.urlopen(req, timeout=600) as r, open(path + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(path + ".part", path)
            return path
        except Exception as e:  # try the next mirror
            print("  failed:", e, flush=True)
            last = e
    raise SystemExit(f"could not download {name}: {last}")


def natural_earth():
    z = fetch(NE_URLS, "HYP_HR_SR_OB_DR.zip")
    with zipfile.ZipFile(z) as zf:
        tif = next(n for n in zf.namelist() if n.lower().endswith(".tif"))
        im = Image.open(io.BytesIO(zf.read(tif))).convert("RGB")
    print("natural earth", im.size, flush=True)
    return im


def etopo(shape_hw):
    """Elevation in metres, resampled to (h, w), equirectangular, north up, lon -180..180."""
    import tifffile
    try:
        a = tifffile.imread(fetch(ETOPO_URLS[:1], "etopo.tif"))
    except BaseException:
        z = fetch(ETOPO_URLS[1:], "etopo1.zip")
        with zipfile.ZipFile(z) as zf:
            tif = next(n for n in zf.namelist() if n.lower().endswith(".tif"))
            a = tifffile.imread(io.BytesIO(zf.read(tif)))
    a = np.asarray(a, dtype=np.float32)
    if a.ndim == 3:
        a = a[..., 0]
    print("etopo", a.shape, float(a.min()), float(a.max()), flush=True)
    h, w = shape_hw
    im = Image.fromarray(a, mode="F").resize((w, h), Image.BILINEAR)
    return np.asarray(im, dtype=np.float32)


def hillshade(elev, exag, lat_rows):
    """Multi-directional hillshade (0..1, 0.5 = flat) of an equirectangular elevation grid."""
    h, w = elev.shape
    R = 6371000.0
    dy = math.pi * R / h                                   # metres per row
    coslat = np.cos(np.radians(lat_rows))[:, None].clip(0.05, 1)
    dx = (2 * math.pi * R / w) * coslat                    # metres per column (shrinks toward the poles)
    gy = (np.roll(elev, -1, 0) - np.roll(elev, 1, 0)) / (2 * dy)
    gx = (np.roll(elev, -1, 1) - np.roll(elev, 1, 1)) / (2 * dx)
    gx *= exag; gy *= exag
    out = np.zeros_like(elev)
    wsum = 0.0
    for az, alt, wt in ((315, 45, 0.5), (270, 50, 0.2), (0, 50, 0.15), (225, 55, 0.15)):
        a, b = math.radians(az), math.radians(alt)
        lx, ly, lz = math.sin(a) * math.cos(b), math.cos(a) * math.cos(b), math.sin(b)
        n = np.sqrt(gx * gx + gy * gy + 1)
        out += wt * ((-gx * lx + gy * ly + lz) / n)        # north is up (row 0), so +gy faces south
        wsum += wt
    out /= wsum
    flat = math.sin(math.radians(48))
    return np.clip(0.5 + (out - flat) * 0.9, 0, 1)


def enhance(rgb, elev, strength=0.55, exag=6.0):
    """Darken shadowed slopes / brighten lit slopes in proportion to real elevation change."""
    h, w = elev.shape
    lat = 90 - (np.arange(h) + 0.5) * 180 / h
    hs = hillshade(elev, exag, lat)
    land = (elev > 0).astype(np.float32)
    # more effect on high, rugged ground; a little on the seafloor too
    height_w = np.clip(elev / 2500.0, 0, 1) * 0.5 + 0.5
    k = strength * land * height_w
    f = 1 + (hs - 0.5) * 2 * k
    out = np.asarray(rgb, dtype=np.float32) * f[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def ocean_lut(cur4k, elev4k):
    """Depth -> colour table taken from the app's current texture, so the seas keep the Atlas's deep blues."""
    c = np.asarray(cur4k, dtype=np.float32).reshape(-1, 3)
    e = elev4k.reshape(-1)
    bins = np.arange(0, 11100, 100)
    lut = np.zeros((len(bins), 3), np.float32)
    last = np.array([170, 210, 230], np.float32)
    for i, d in enumerate(bins):
        m = (e <= -d) & (e > -d - 100)
        if m.sum() > 50:
            last = np.median(c[m], axis=0)
        lut[i] = last
    return lut


def base(ne, elev, cur4k):
    """Natural Earth land at full resolution; seas recoloured by real depth in the current texture's palette,
    with the seafloor ridges and trenches shaded."""
    h, w = elev.shape
    e4 = np.asarray(Image.fromarray(elev, mode="F").resize(cur4k.size, Image.BILINEAR))
    lut = ocean_lut(cur4k, e4)
    rgb = np.asarray(ne, dtype=np.float32)
    depth = np.clip(-elev, 0, 11000) / 100.0
    i0 = np.floor(depth).astype(int).clip(0, len(lut) - 1); i1 = (i0 + 1).clip(0, len(lut) - 1)
    f = (depth - i0)[..., None]
    sea = lut[i0] * (1 - f) + lut[i1] * f
    lat = 90 - (np.arange(h) + 0.5) * 180 / h
    hs = hillshade(elev, 18.0, lat)
    sea *= (1 + (hs - 0.5) * 1.1)[..., None]
    watery = (rgb[..., 2] > rgb[..., 0] + 12) & (elev < 0)       # Natural Earth paints it as water and it is below sea level
    # soften the edge so coastlines stay smooth
    m = Image.fromarray((watery * 255).astype(np.uint8)).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(1.2))
    m = (np.asarray(m, np.float32) / 255.0)[..., None]
    out = rgb * (1 - m) + sea * m
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ orthographic renderer (same math as the app's shader)
def render(tex, lon0, lat0, R, W=1080, H=1400):
    t = np.asarray(tex, dtype=np.float32)
    th, tw = t.shape[:2]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    sx = (xs - W / 2) / R
    sy = -(ys - H / 2) / R
    d2 = sx * sx + sy * sy
    inside = d2 <= 1
    X = np.sqrt(np.clip(1 - d2, 0, 1))
    p = math.radians(lat0)
    cp, sp = math.cos(p), math.sin(p)
    x = X * cp - sy * sp
    z = sy * cp + X * sp
    y = sx
    lon = np.degrees(np.arctan2(y, x)) + lon0
    lat = np.degrees(np.arcsin(np.clip(z, -1, 1)))
    u = ((lon + 180) % 360) / 360 * tw - 0.5
    v = (90 - lat) / 180 * th - 0.5
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
    fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    u1 = (u0 + 1) % tw; u0 %= tw
    v0c = v0.clip(0, th - 1); v1c = (v0 + 1).clip(0, th - 1)
    c = (t[v0c, u0] * (1 - fu) * (1 - fv) + t[v0c, u1] * fu * (1 - fv)
         + t[v1c, u0] * (1 - fu) * fv + t[v1c, u1] * fu * fv)
    c *= (0.72 + 0.28 * np.clip(X / 0.6, 0, 1))[..., None]
    bg = np.array([12, 17, 23], np.float32)
    c = np.where(inside[..., None], c, bg)
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))


VIEWS = [  # name, lon, lat, zoom (the app's k), label
    ("himalaya", 86.9, 28.6, 7.5, "Himalayas and Mount Everest"),
    ("alps", 8.6, 46.2, 7.5, "The Alps"),
    ("andes", -69.5, -24.0, 7.5, "The Andes (Atacama)"),
    ("rockies", -107.5, 39.5, 7.5, "The Rocky Mountains"),
    ("mideast", 44.0, 32.0, 3.5, "Middle East, medium zoom"),
]
BASE_R = 190 * 3      # a typical phone: globe radius 190 CSS px at 3x pixel density


def label(im, text):
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except Exception:
        f = ImageFont.load_default()
    d.rectangle([0, 0, im.width, 70], fill=(12, 17, 23))
    d.text((24, 14), text, font=f, fill=(240, 244, 248))
    return im


def preview(out, current_4k):
    os.makedirs(out, exist_ok=True)
    ne0 = natural_earth()
    elev = etopo((ne0.height, ne0.width))
    cur = Image.open(current_4k).convert("RGB")
    ne = base(ne0, elev, cur)
    rich = enhance(ne, elev)
    meta = []
    for name, lon, lat, k, title in VIEWS:
        R = BASE_R * k
        a = label(render(cur, lon, lat, R), "Now (4k)")
        b = label(render(ne, lon, lat, R), "Sharper (21k)")
        c = label(render(rich, lon, lat, R), "Sharper + elevation relief")
        sheet = Image.new("RGB", (a.width * 3 + 40, a.height), (12, 17, 23))
        for i, im in enumerate((a, b, c)):
            sheet.paste(im, (i * (a.width + 20), 0))
        sheet.save(os.path.join(out, f"{name}.jpg"), quality=88)
        for tag, im in (("now", a), ("sharp", b), ("relief", c)):
            im.save(os.path.join(out, f"{name}-{tag}.jpg"), quality=88)
        meta.append({"name": name, "title": title, "lon": lon, "lat": lat, "zoom": k})
        print("preview", name, flush=True)
    json.dump(meta, open(os.path.join(out, "views.json"), "w"), indent=1)


def tiles(out, mode):
    os.makedirs(out, exist_ok=True)
    ne0 = natural_earth()
    elev = etopo((ne0.height, ne0.width))
    full = base(ne0, elev, Image.open(os.environ.get("CURRENT_4K", "earth-relief-4k.jpg")).convert("RGB"))
    if mode == "relief":
        full = enhance(full, elev)
    big = full.resize((16384, 8192), Image.LANCZOS)
    full.resize((4096, 2048), Image.LANCZOS).save(os.path.join(out, "earth-relief-4k.jpg"), quality=86)
    full.resize((2048, 1024), Image.LANCZOS).save(os.path.join(out, "earth-relief-2k.jpg"), quality=86)
    td = os.path.join(out, "relief-tiles")
    os.makedirs(td, exist_ok=True)
    for ty in range(4):
        for tx in range(8):
            big.crop((tx * 2048, ty * 2048, tx * 2048 + 2048, ty * 2048 + 2048)).save(
                os.path.join(td, f"{tx}_{ty}.jpg"), quality=84, optimize=True, progressive=False)
    print("tiles done", flush=True)


if __name__ == "__main__":
    cmd, out = sys.argv[1], sys.argv[2]
    if cmd == "preview":
        preview(out, sys.argv[3] if len(sys.argv) > 3 else "earth-relief-4k.jpg")
    else:
        tiles(out, sys.argv[3] if len(sys.argv) > 3 else "relief")

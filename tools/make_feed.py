"""Turn an export of the Dateline Atlas database into data/feed.json for this site.

python3 tools/make_feed.py <export-dir> data/feed.json

<export-dir> is a folder written by ArtifactData with out_dir: it holds events/<id>.json
(one file per story) and meta/status.json. Stories whose expiresAt has passed are left out.
"""
import datetime, json, pathlib, sys

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
now = datetime.datetime.now(datetime.timezone.utc)

def expired(d):
    try:
        exp = datetime.datetime.fromisoformat(str(d.get("expiresAt", "")).replace("Z", "+00:00"))
        return exp < now
    except ValueError:
        return False

events = []
for f in sorted((src / "events").glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    if isinstance(data, dict) and not expired(data):
        events.append({"id": f.stem, "data": data})
meta_file = src / "meta" / "status.json"
meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else None

feed = {"generatedAt": now.isoformat(timespec="seconds").replace("+00:00", "Z"), "meta": meta, "events": events}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(feed, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"{len(events)} stories -> {out}")

from pathlib import Path
import struct
import plistlib
from logicx.projectdata import ProjectData, _u32

bundle = Path(r"C:\dev\daw2logic\Dawprojects\Find a way JP.logicx")
pd_bytes = (bundle / "Alternatives/000/ProjectData").read_bytes()
pd = ProjectData.parse(pd_bytes)

with open(bundle / "Alternatives/000/MetaData.plist", "rb") as f:
    meta = plistlib.load(f)

sample_rate = meta.get("SampleRate", 44100)
tempo = 120.0  # default / standard

print("=" * 60)
print(f"EXTRACTING LOGIC SESSION (Sample Rate: {sample_rate} Hz)")
print("=" * 60)

# 1. Map Track Index -> Track Name (from ivnE records)
IVNE_NAME_LEN = 0x2c
IVNE_NAME = 0x2e
track_names = {}
# Find all arrange audio tracks in karT order
chan_pos = {}
pos = 0
for r in pd.records:
    if r.tag == b"karT" and len(r.raw) == 93 and _u32(r.raw, 0x08) == 0x040000:
        ch = _u32(r.raw, 0x2a)
        if ch != 0x500000: # not master
            pos += 1
            chan_pos[ch] = pos

for ch, t_idx in sorted(chan_pos.items(), key=lambda x: x[1]):
    iv = next((r for r in pd.records if r.tag == b"ivnE" and _u32(r.raw, 0x08) == ch), None)
    if iv:
        try:
            p = iv.raw[0x24:]
            nlen = struct.unpack_from("<H", p, 0x08)[0]
            name = p[0x0a:0x0a + nlen].decode("latin-1", "replace")
            track_names[t_idx] = name
        except Exception:
            track_names[t_idx] = f"Audio {t_idx}"

print(f"Total arrange tracks found: {len(track_names)}")
for t_idx, name in list(track_names.items())[:8]:
    print(f"  Track {t_idx:<2}: {name}")

# 2. Extract Audio Regions
by_idx = pd._region_records_by_index()
placements = list(pd.audio_placements())

extracted_regions = []
for ev in placements:
    r_idx = ev["region_index"]
    track = ev["track"]
    tick = ev["pos"] - 34560
    
    # Filename from lFuA
    li = by_idx.get(r_idx, {}).get("lFuA")
    fname = ""
    if li is not None:
        p = pd.records[li].raw[0x24:]
        nlen = struct.unpack_from("<H", p, 0x08)[0]
        fname = p[0x0a:0x0a + nlen * 2].decode("utf-16-le", "replace")
        
    # Sample length & Region Name from gRuA
    gi = by_idx.get(r_idx, {}).get("gRuA")
    frames = 0
    reg_name = ""
    if gi is not None:
        raw = pd.records[gi].raw
        # sample length uint32 at 0x3a
        frames = struct.unpack_from("<I", raw, 0x24 + 0x16)[0]
        # name at 0x24 + 0x4a
        try:
            n_len = struct.unpack_from("<H", raw, 0x24 + 0x4a)[0]
            reg_name = raw[0x24 + 0x4c:0x24 + 0x4c + n_len].decode("latin-1", "replace")
        except Exception:
            pass
            
    extracted_regions.append({
        "track": track,
        "tick": tick,
        "frames": frames,
        "seconds": round(frames / sample_rate, 3) if frames else 0,
        "name": reg_name,
        "file": fname
    })

print(f"\nTotal regions extracted: {len(extracted_regions)}")
print("\nSample 3 extracted regions:")
for r in extracted_regions[:3]:
    print(f"  Track {r['track']} ({track_names.get(r['track'], 'Unknown')}) | Tick: {r['tick']:<6} | Duration: {r['seconds']}s | File: {r['file']}")
print("=" * 60)

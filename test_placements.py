from pathlib import Path
import struct
from logicx.projectdata import ProjectData

bundle = Path(r"C:\dev\daw2logic\Dawprojects\Find a way JP.logicx")
pd = ProjectData.parse((bundle / "Alternatives/000/ProjectData").read_bytes())

print("=" * 45)
print("TESTING AUDIO PLACEMENTS & FILENAMES")
print("=" * 45)

by_idx = pd._region_records_by_index()
placements = list(pd.audio_placements())
print(f"Total audio placement events found: {len(placements)}")

if placements:
    print(f"\nSample placement event #0:\n{placements[0]}")
    
    # Check how many have linked filenames
    resolved = 0
    sample_files = []
    for ev in placements:
        li = by_idx.get(ev["region_index"], {}).get("lFuA")
        if li is not None:
            p = pd.records[li].raw[0x24:]
            nlen = struct.unpack_from("<H", p, 0x08)[0]
            fname = p[0x0a:0x0a + nlen * 2].decode("utf-16-le", "replace")
            resolved += 1
            if len(sample_files) < 5:
                sample_files.append((ev.get("track"), ev.get("pos"), fname))
                
    print(f"\nSuccessfully resolved filenames for {resolved} of {len(placements)} regions.")
    print("\nFirst 5 timeline mappings (Track, Tick, Filename):")
    for t, pos, fn in sample_files:
        print(f"  Track {t:<2} | Tick {pos:<8} | File: {fn}")
print("=" * 45)

import struct
from pathlib import Path
from logicx.projectdata import ProjectData, _u32

bundle = Path(r"C:\dev\daw2logic\Dawprojects\Find a way JP.logicx")
pd = ProjectData.parse((bundle / "Alternatives/000/ProjectData").read_bytes())

print("=" * 60)
print("ALL CHANNELS IN LOGIC SESSION:")
iv_count = 0
for r in pd.records:
    if r.tag == b"ivnE":
        chan = _u32(r.raw, 0x08)
        nlen = struct.unpack_from("<H", r.raw, 0xc2)[0] if len(r.raw) > 0xc4 else 0
        name = r.raw[0xc4:0xc4 + nlen].decode("latin-1", "replace") if nlen else ""
        if name:
            iv_count += 1
            if iv_count <= 10:
                print(f"  Channel 0x{chan:06x} -> '{name}'")
print(f"Total named channels found: {iv_count}")
print("=" * 60)

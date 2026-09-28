import struct
from pathlib import Path
from logicx.projectdata import ProjectData, _u32

bundle = Path(r"C:\dev\daw2logic\Dawprojects\Find a way JP.logicx")
pd = ProjectData.parse((bundle / "Alternatives/000/ProjectData").read_bytes())

print("=" * 60)
print("AUDIO TRACK CHANNELS (> 0x500000):")
for r in pd.records:
    if r.tag == b"ivnE":
        chan = _u32(r.raw, 0x08)
        if chan > 0x500000:
            nlen = struct.unpack_from("<H", r.raw, 0xc2)[0] if len(r.raw) > 0xc4 else 0
            name = r.raw[0xc4:0xc4 + nlen].decode("latin-1", "replace") if nlen else "No name"
            print(f"  Channel 0x{chan:06x} -> '{name}'")
print("=" * 60)

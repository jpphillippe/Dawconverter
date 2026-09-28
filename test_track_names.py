from pathlib import Path
import struct
from logicx.projectdata import ProjectData

bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())

print('Extracting Track Names from Logic ivnE records:\n')
track_names = []
for r in pd.records:
    if r.tag == b'ivnE' and len(r.raw) > 0xc4:
        n = struct.unpack_from('<H', r.raw, 0xc2)[0]
        if 0 < n < 100:
            name = r.raw[0xc4:0xc4 + n].decode('latin-1', 'replace')
            track_names.append(name)

for i, name in enumerate(track_names):
    print(f'Track #{i+1:<2}: {name}')

import struct
from pathlib import Path
from logicx.projectdata import ProjectData

bundle = Path(r'C:\dev\daw2logic\Dawprojects\Find a way JP.logicx')
pd = ProjectData.parse((bundle / 'Alternatives/000/ProjectData').read_bytes())
slots_by_idx = pd._region_records_by_index()

print('Checking first 10 regions in Logic lFuA records:')
for reg_idx in range(10):
    slots = slots_by_idx.get(reg_idx)
    if slots and 'lFuA' in slots:
        r = pd.records[slots['lFuA']]
        # Read UTF-16LE filename from lFuA
        # Offset 0x24 + length @ 0x3e
        fn_bytes = r.raw[0x24:]
        fn = ''
        for off in range(0x30, len(r.raw) - 4, 2):
            chunk = r.raw[off:off+40].decode('utf-16le', 'ignore').split('\x00')[0]
            if chunk.endswith('.wav'):
                fn = chunk
                break
        print(f'  Region {reg_idx:<3}: File = {fn}')

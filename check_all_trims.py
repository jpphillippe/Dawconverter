import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

trimmed_clips = []
for c in orig.findall('.//Clip'):
    ps = c.get('playStart')
    name = c.get('name')
    if ps and float(ps) > 0.01:
        trimmed_clips.append((name, c.get('time'), ps, c.get('duration')))

print(f'Total clips with playStart / source trim: {len(trimmed_clips)}\n')
for name, t, ps, dur in trimmed_clips[:15]:
    print(f'  Clip: {name:<25} | at beat: {t:<5} | playStart: {ps:<6} | duration: {dur}')

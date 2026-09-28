import zipfile, xml.etree.ElementTree as ET

with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP_from_logic.dawproject') as z:
    gen = ET.fromstring(z.read('project.xml'))

# Check Tempo
orig_tempo_el = orig.find('.//Transport/Tempo')
orig_tempo = orig_tempo_el.get('value') if orig_tempo_el is not None else None
gen_tempo_el = gen.find('.//Transport/Tempo')
gen_tempo = gen_tempo_el.get('value') if gen_tempo_el is not None else None

print('Original Tempo:', orig_tempo)
print('Generated Tempo:', gen_tempo)

# Check Master Track / Routing
print('\nOriginal Tracks (Master & Smash):')
for t in orig.findall('.//Structure/Track'):
    ch = t.find('Channel')
    role = ch.get('role') if ch is not None else 'no channel'
    dest = ch.get('destination') if ch is not None else 'no dest'
    ch_id = ch.get('id') if ch is not None else ''
    tname = t.get('name')
    if role == 'master' or tname == 'Smash (R)':
        print('  Track:', tname, '| role:', role, '| id:', ch_id, '| dest:', dest)

# Compare first 5 clips on Track 1 (Smash)
print('\nOriginal Smash (R) Clips:')
orig_lane = orig.find('.//Arrangement//Lanes[@track]')
if orig_lane is not None:
    for c in orig_lane.findall('.//Clip')[:5]:
        print('  time:', c.get('time'), '| dur:', c.get('duration'), '| name:', c.get('name'))

print('\nGenerated Smash (R) Clips:')
gen_lane = gen.find('.//Arrangement//Lanes[@track]')
if gen_lane is not None:
    for c in gen_lane.findall('.//Clip')[:5]:
        print('  time:', c.get('time'), '| dur:', c.get('duration'), '| name:', c.get('name'))

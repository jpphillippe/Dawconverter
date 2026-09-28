import zipfile, xml.etree.ElementTree as ET

with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    orig = ET.fromstring(z.read('project.xml'))

with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP_from_logic.dawproject') as z:
    gen = ET.fromstring(z.read('project.xml'))

# 1. Compare Channel XML
orig_chan = orig.find('.//Channel')
gen_chan = gen.find('.//Channel')
print('=== ORIGINAL CHANNEL XML ===')
print(ET.tostring(orig_chan, encoding='unicode'))
print('=== GENERATED CHANNEL XML ===')
print(ET.tostring(gen_chan, encoding='unicode'))

# 2. Compare Clip XML
orig_clip = orig.find('.//Clip')
gen_clip = gen.find('.//Clip')
print('\n=== ORIGINAL CLIP XML ===')
print(ET.tostring(orig_clip, encoding='unicode'))
print('=== GENERATED CLIP XML ===')
print(ET.tostring(gen_clip, encoding='unicode'))

# 3. Compare Arrangement / Lanes hierarchy
orig_arr = orig.find('.//Arrangement')
print('\n=== ORIGINAL ARRANGEMENT HIERARCHY ===')
for elem in orig_arr.iter():
    if elem.tag in ('Arrangement', 'Lanes', 'Clips', 'Clip'):
        print(f'{elem.tag}: attrib={elem.attrib}')
        if elem.tag == 'Clip':
            break

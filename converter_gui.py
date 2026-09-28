import sys, os, struct, plistlib, zipfile, wave, threading
from pathlib import Path
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Import core dependencies
from logicx.projectdata import ProjectData, IVNE_IDX, _u32
from daw2logic.track_order import audio_channels
from daw2logic.convert import convert_file

# ==============================================================================
# LOGIC -> DAWPROJECT CONVERSION ENGINE
# ==============================================================================
def run_logic_to_daw(logicx_dir: Path, out_dawproject: Path, status_cb):
    status_cb('Reading Logic Pro bundle...')
    meta_path = logicx_dir / 'Alternatives/000/MetaData.plist'
    meta = plistlib.loads(meta_path.read_bytes())
    tempo = float(meta.get('BeatsPerMinute', 120.0))
    sample_rate = int(meta.get('SampleRate', 44100))
    ts_num = int(meta.get('SongSignatureNumerator', 4))
    ts_den = int(meta.get('SongSignatureDenominator', 4))

    pd_path = logicx_dir / 'Alternatives/000/ProjectData'
    pd = ProjectData.parse(pd_path.read_bytes())
    slots_by_idx = pd._region_records_by_index()

    status_cb('Resolving track names and mixer buses...')
    aud_map = audio_channels(pd)
    track_names = {}
    for track_num, chan_id in aud_map.items():
        iv = next((r for r in pd.records if r.tag == b'ivnE' and _u32(r.raw, IVNE_IDX) == chan_id), None)
        if iv and len(iv.raw) > 0xc4:
            n = struct.unpack_from('<H', iv.raw, 0xc2)[0]
            name = iv.raw[0xc4:0xc4 + n].decode('latin-1', 'replace').strip()
            track_names[track_num] = name if name else f'Audio {track_num}'
        else:
            track_names[track_num] = f'Audio {track_num}'

    placements = pd.audio_placements()
    clips_by_track = {}
    for p in placements:
        clips_by_track.setdefault(p['track'], []).append(p)

    status_cb(f'Constructing DAWproject XML ({len(placements)} regions across {len(track_names)} tracks)...')
    root = ET.Element('Project', version='1.0')
    ET.SubElement(root, 'Application', name='Logic-DAWproject-Bridge', version='1.0.0')

    transport = ET.SubElement(root, 'Transport')
    ET.SubElement(transport, 'Tempo', value=str(tempo))
    ET.SubElement(transport, 'TimeSignature', numerator=str(ts_num), denominator=str(ts_den))

    structure = ET.SubElement(root, 'Structure')
    # Stereo Out Master Channel (unmutes tracks in Cubase)
    master_chan = ET.SubElement(structure, 'Channel', role='master', audioChannels='2', id='master_out', name='Stereo Out', color='#90a0b0ff')
    ET.SubElement(master_chan, 'Mute', value='false', name='Mute')
    ET.SubElement(master_chan, 'Pan', value='0.5', unit='normalized', min='0', max='1', name='Pan')
    ET.SubElement(master_chan, 'Volume', value='1', unit='linear', min='0', max='2', name='Volume')

    for t_num in sorted(track_names.keys()):
        t_id = f'track_{t_num}'
        t_el = ET.SubElement(structure, 'Track', id=t_id, name=track_names[t_num], contentType='audio')
        ch = ET.SubElement(t_el, 'Channel', role='regular', audioChannels='2', id=f'chan_{t_num}', name=track_names[t_num], destination='master_out')
        ET.SubElement(ch, 'Mute', value='false', name='Mute')
        ET.SubElement(ch, 'Pan', value='0.5', unit='normalized', min='0', max='1', name='Pan')
        ET.SubElement(ch, 'Volume', value='1', unit='linear', min='0', max='2', name='Volume')

    arrang = ET.SubElement(root, 'Arrangement')
    master_lanes = ET.SubElement(arrang, 'Lanes', timeUnit='seconds')
    used_wav_files = set()

    for t_num in sorted(track_names.keys()):
        t_id = f'track_{t_num}'
        track_lanes = ET.SubElement(master_lanes, 'Lanes', track=t_id)
        clips_container = ET.SubElement(track_lanes, 'Clips')

        for p in clips_by_track.get(t_num, []):
            start_ticks = max(0, p['pos'] - 34560)
            start_beats = round(start_ticks / 960.0, 6)
            clip_time_str = str(int(start_beats) if start_beats.is_integer() else start_beats)

            reg_idx = p['region_index']
            slots = slots_by_idx.get(reg_idx)
            if not slots or 'lFuA' not in slots:
                continue

            r = pd.records[slots['lFuA']]
            nlen = struct.unpack_from('<H', r.raw, 0x24 + 0x08)[0]
            wav_filename = r.raw[0x24 + 0x0a : 0x24 + 0x0a + nlen * 2].decode('utf-16le', 'ignore')

            disk_wav = logicx_dir / 'Media' / 'Audio Files' / wav_filename
            used_wav_files.add(disk_wav)

            sample_len = 0
            if 'gRuA' in slots:
                gr = pd.records[slots['gRuA']]
                sample_len = struct.unpack_from('<I', gr.raw, 0x24 + pd.GRUA_SAMPLELEN_OFF)[0]

            duration_sec = round(sample_len / float(sample_rate), 6) if sample_len > 0 else 2.0
            
            # Clean display name (strips internal slice hashes for clean DAW timeline view)
            display_name = wav_filename.split('_')[0] if '_' in wav_filename else Path(wav_filename).stem

            outer_clip = ET.SubElement(clips_container, 'Clip', time=clip_time_str, duration=str(duration_sec), fadeTimeUnit='seconds', name=display_name, enable='true')
            nested_clips = ET.SubElement(outer_clip, 'Clips')
            inner_clip = ET.SubElement(nested_clips, 'Clip', contentTimeUnit='seconds', time='0', duration=str(duration_sec))
            audio_el = ET.SubElement(inner_clip, 'Audio', sampleRate=str(sample_rate), channels='2', duration=str(duration_sec))
            ET.SubElement(audio_el, 'File', path=f'audio/{wav_filename}', external='false')

    meta_root = ET.Element('MetaData', version='1.0')
    ET.SubElement(meta_root, 'Title').text = logicx_dir.stem

    ET.indent(root, space='  ')
    ET.indent(meta_root, space='  ')

    status_cb(f'Packaging {len(used_wav_files)} audio files into .dawproject container...')
    with zipfile.ZipFile(out_dawproject, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('project.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
        z.writestr('metadata.xml', ET.tostring(meta_root, encoding='utf-8', xml_declaration=True))
        for wav_path in used_wav_files:
            if wav_path.exists():
                z.write(wav_path, arcname=f'audio/{wav_path.name}')

# ==============================================================================
# DAWPROJECT -> LOGIC CONVERSION ENGINE
# ==============================================================================
def run_daw_to_logic(dawproject_file: Path, out_logicx: Path, status_cb):
    status_cb('Unpacking DAWproject & preparing stems...')
    convert_file(dawproject_file, out_logicx, force=True)

# ==============================================================================
# MODERN DARK UI (TKINTER)
# ==============================================================================
class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('DAWproject ? Logic Pro Converter')
        self.geometry('680x450')
        self.resizable(False, False)
        self.configure(bg='#1e1e1e')

        self.mode = tk.StringVar(value='DAW_TO_LOGIC')
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status_text = tk.StringVar(value='Ready. Choose conversion mode and select project.')

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg='#252526', height=60)
        header.pack(fill='x', side='top')
        title = tk.Label(header, text='AUDIO PROJECT BRIDGE', font=('Segoe UI', 15, 'bold'), fg='#007acc', bg='#252526')
        title.pack(pady=5)
        subtitle = tk.Label(header, text='Fast, Lossless 2-Way Conversion (Client-Side)', font=('Segoe UI', 9), fg='#858585', bg='#252526')
        subtitle.pack()

        # Mode Selector
        mode_frame = tk.Frame(self, bg='#1e1e1e')
        mode_frame.pack(pady=15)

        self.rb1 = tk.Radiobutton(mode_frame, text='Cubase / DAWproject  ?  Logic Pro (.logicx)', variable=self.mode,
                                  value='DAW_TO_LOGIC', font=('Segoe UI', 10, 'bold'), fg='white', bg='#1e1e1e',
                                  selectcolor='#007acc', activebackground='#1e1e1e', activeforeground='white',
                                  command=self._on_mode_change)
        self.rb1.pack(side='left', padx=15)

        self.rb2 = tk.Radiobutton(mode_frame, text='Logic Pro (.logicx)  ?  DAWproject (.dawproject)', variable=self.mode,
                                  value='LOGIC_TO_DAW', font=('Segoe UI', 10, 'bold'), fg='white', bg='#1e1e1e',
                                  selectcolor='#007acc', activebackground='#1e1e1e', activeforeground='white',
                                  command=self._on_mode_change)
        self.rb2.pack(side='left', padx=15)

        # File Pickers Card
        card = tk.Frame(self, bg='#2d2d30', padx=15, pady=15)
        card.pack(fill='x', padx=30, pady=5)

        # Input Row
        self.lbl_in = tk.Label(card, text='Input DAWproject File:', font=('Segoe UI', 9, 'bold'), fg='#d4d4d4', bg='#2d2d30')
        self.lbl_in.grid(row=0, column=0, sticky='w', pady=3)
        self.entry_in = tk.Entry(card, textvariable=self.input_path, width=54, bg='#1e1e1e', fg='white', insertbackground='white')
        self.entry_in.grid(row=1, column=0, padx=(0, 10), pady=(0, 10))
        btn_in = tk.Button(card, text='Browse...', width=10, bg='#3e3e42', fg='white', relief='flat', command=self._browse_input)
        btn_in.grid(row=1, column=1, pady=(0, 10))

        # Output Row
        self.lbl_out = tk.Label(card, text='Output Logic Bundle:', font=('Segoe UI', 9, 'bold'), fg='#d4d4d4', bg='#2d2d30')
        self.lbl_out.grid(row=2, column=0, sticky='w', pady=3)
        self.entry_out = tk.Entry(card, textvariable=self.output_path, width=54, bg='#1e1e1e', fg='white', insertbackground='white')
        self.entry_out.grid(row=3, column=0, padx=(0, 10))
        btn_out = tk.Button(card, text='Save To...', width=10, bg='#3e3e42', fg='white', relief='flat', command=self._browse_output)
        btn_out.grid(row=3, column=1)

        # Convert Action Button
        self.btn_convert = tk.Button(self, text='START CONVERSION', font=('Segoe UI', 11, 'bold'), bg='#0e639c', fg='white',
                                     relief='flat', height=2, cursor='hand2', command=self._start_conversion)
        self.btn_convert.pack(fill='x', padx=30, pady=20)

        # Status Bar
        status_bar = tk.Frame(self, bg='#007acc', height=24)
        status_bar.pack(fill='x', side='bottom')
        lbl_status = tk.Label(status_bar, textvariable=self.status_text, font=('Segoe UI', 8, 'bold'), fg='white', bg='#007acc')
        lbl_status.pack(side='left', padx=10)

    def _on_mode_change(self):
        self.input_path.set('')
        self.output_path.set('')
        if self.mode.get() == 'DAW_TO_LOGIC':
            self.lbl_in.config(text='Input DAWproject File (.dawproject):')
            self.lbl_out.config(text='Output Logic Pro Bundle (.logicx):')
        else:
            self.lbl_in.config(text='Input Logic Pro Folder (.logicx):')
            self.lbl_out.config(text='Output DAWproject File (.dawproject):')

    def _browse_input(self):
        if self.mode.get() == 'DAW_TO_LOGIC':
            fn = filedialog.askopenfilename(title='Select .dawproject file', filetypes=[('DAWproject files', '*.dawproject')])
            if fn:
                self.input_path.set(fn)
                self.output_path.set(fn.replace('.dawproject', '.logicx'))
        else:
            fn = filedialog.askdirectory(title='Select .logicx folder (or extracted project)')
            if fn:
                self.input_path.set(fn)
                p = Path(fn)
                out_name = p.stem.replace('.logicx', '') + '_from_logic.dawproject'
                self.output_path.set(str(p.parent / out_name))

    def _browse_output(self):
        if self.mode.get() == 'DAW_TO_LOGIC':
            fn = filedialog.asksaveasfilename(title='Save Logic Project As', filetypes=[('Logic Pro Projects', '*.logicx')])
            if fn:
                if not fn.endswith('.logicx'): fn += '.logicx'
                self.output_path.set(fn)
        else:
            fn = filedialog.asksaveasfilename(title='Save DAWproject As', filetypes=[('DAWproject files', '*.dawproject')])
            if fn:
                if not fn.endswith('.dawproject'): fn += '.dawproject'
                self.output_path.set(fn)

    def _start_conversion(self):
        inp = self.input_path.get().strip()
        out = self.output_path.get().strip()
        if not inp or not out:
            messagebox.showwarning('Missing Paths', 'Please choose both an input and an output location.')
            return

        self.btn_convert.config(state='disabled', text='CONVERTING... PLEASE WAIT')
        threading.Thread(target=self._worker, args=(inp, out), daemon=True).start()

    def _worker(self, inp, out):
        try:
            mode = self.mode.get()
            if mode == 'DAW_TO_LOGIC':
                run_daw_to_logic(Path(inp), Path(out), lambda msg: self.status_text.set(msg))
            else:
                run_logic_to_daw(Path(inp), Path(out), lambda msg: self.status_text.set(msg))

            self.status_text.set('Success! Conversion completed.')
            messagebox.showinfo('Complete', f'Successfully converted to:\n{out}')
        except Exception as e:
            self.status_text.set('Error during conversion.')
            messagebox.showerror('Conversion Failed', str(e))
        finally:
            self.btn_convert.config(state='normal', text='START CONVERSION')

if __name__ == '__main__':
    app = ConverterApp()
    app.mainloop()

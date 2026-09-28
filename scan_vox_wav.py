import zipfile, wave, struct

# 1. Read Vox Chop-02.wav directly from the original DAWproject
with zipfile.ZipFile(r'C:\dev\daw2logic\Dawprojects\Find a way JP.dawproject') as z:
    for name in z.namelist():
        if 'vox chop-02' in name.lower() and name.endswith('.wav'):
            wav_data = z.read(name)
            wav_name = name
            break

print(f'Scanning: {wav_name} ({len(wav_data)} bytes)\n')

# 2. Extract and analyze frames in 4-second blocks
import io
wf = wave.open(io.BytesIO(wav_data), 'rb')
rate = wf.getframerate()
channels = wf.getnchannels()
sampwidth = wf.getsampwidth()
total_frames = wf.getnframes()
total_sec = total_frames / rate

print(f'Sample Rate: {rate} Hz | Channels: {channels} | Total Length: {total_sec:.2f} seconds')
print('-' * 60)
print(f'{"Time Range":<18} | {"Peak Level":<12} | Waveform Status')
print('-' * 60)

block_sec = 4.0
block_frames = int(block_sec * rate)
for start_f in range(0, total_frames, block_frames):
    sec = start_f / rate
    bar_approx = (sec * 2.0 / 4.0) + 1.0  # at 120 BPM
    n = min(block_frames, total_frames - start_f)
    frames = wf.readframes(n)
    
    # Calculate peak volume
    if sampwidth == 2:
        samples = struct.unpack(f'<{n * channels}h', frames)
        peak = max(abs(s) for s in samples) if samples else 0
        peak_norm = peak / 32768.0
    elif sampwidth == 3:
        peak = 0
        for i in range(0, len(frames), 3):
            val = abs(int.from_bytes(frames[i:i+3], 'little', signed=True))
            if val > peak: peak = val
        peak_norm = peak / 8388608.0
    else:
        peak_norm = 0.0

    if peak_norm > 0.1:
        status = '### ACTIVE VOCAL ###'
    elif peak_norm > 0.01:
        status = '... quiet/low sound ...'
    else:
        status = '[SILENCE]'

    print(f'{sec:5.1f}s - {sec+block_sec:5.1f}s (Bar {bar_approx:4.1f}) | Peak: {peak_norm:6.3f} | {status}')

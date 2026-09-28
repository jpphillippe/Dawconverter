<img width="500" height="500" alt="icon" src="https://github.com/user-attachments/assets/a9d47fcc-ff0c-4ee2-8bc3-2848684a69cc" />

# DAW-Logic Bridge

**Lossless 2-way project bridge between Cubase / DAWproject (`.dawproject`) and Apple Logic Pro (`.logicx`).**

Available as a standalone desktop GUI app (macOS & Windows), a portable Python CLI, and an experimental in-browser WASM converter.

---

## Why This Exists

Traditional stem bouncing requires rendering every track from Bar 1 to the end of the song. For a 30-track session, this easily balloons to **4 to 6+ GB of dead silence** and slows down client transfers.

**DAW-Logic Bridge** transfers projects with **discrete clip boundaries intact**:
- **Tiny file sizes:** Only actual audio clips are packaged (saving gigabytes of wasted silence).
- **Fast transfers:** Sessions transfer in seconds over standard internet connections.
- **True timeline structure:** Audio regions stay cut, movable, and slip-editable with volume, pan, and mute states preserved.
- **100% Lossless:** Stems transfer at full bit-depth and sample rate with zero compression loss.

---

## Download Standalone Desktop App

No Python, terminal, or dependencies required.

| Platform | Download | Format |
| :--- | :--- | :--- |
| **macOS (Apple Silicon & Intel)** | [Download Latest macOS App](https://github.com/jpphillippe/Dawconverter/actions) | `.app` inside `.zip` |
| **Windows 10 / 11** | [Download Latest Windows App](https://github.com/jpphillippe/Dawconverter/actions) | Standalone `.exe` |

> **First-time opening on macOS (Apple Gatekeeper):**  
> Because the app is open-source and not notarized through an Apple Developer account, macOS will show a security warning if you double-click it.  
> **To open:** Right-click (or Control-click) `DAW-Logic-Bridge.app` -> choose **Open** -> click **Open** in the confirmation dialog. You only need to do this once.

---

## Recommended Studio Workflows

> **Important Note on Plugins & Automation:**  
> Proprietary plugin chains (VST3 vs. Apple AU), channel EQs, and software instruments cannot translate natively between DAWs. **Always bake in synths, plugins, or automation you want preserved before exporting!**

---

### Workflow 1: Logic Pro → Cubase (macOS)

#### Step A: Prepare the Logic Pro Project
1. **Save your project** before starting.
2. **Select all regions on the timeline:**
   - Press `Cmd + A` (or Shift-select the parts you want to render).
3. **Open Bounce in Place:**
   - Right-click any highlighted region and choose **Bounce in Place...** (or press `Ctrl + B`).
4. **Configure the Bounce dialog:**
   - **Destination:** *New Track*
   - **Bypass Effect Plug-ins:** *Uncheck* (bakes synths, AU plugins, and insert FX into the audio).
   - **Include Audio Tail in File:** *Check* (prevents reverb/delay tails from cutting off).
   - **Include Volume/Pan Automation:** *Check* (bakes fader moves into the audio).
   - Click **OK**.
5. Logic will render each region into its own discrete audio clip at its exact timeline position on new audio tracks.
6. Group the newly rendered tracks together, delete or mute the old MIDI/synth tracks, and save your project.

#### Step B: Convert to DAWproject
1. Open **`DAW-Logic-Bridge.app`** (Right-click > Open on first launch).
2. Choose **Logic Pro (.logicx) → DAWproject (.dawproject)**.
3. **Input:** Select your rendered `.logicx` project folder.
4. Click **START CONVERSION**.
5. Send the generated `..._from_logic.dawproject` file to your collaborator. Done!

---

### Workflow 2: Cubase → Logic Pro (Windows)

#### Step A: Prepare the Cubase Project
1. **Save your project** before starting.
2. **Select all parts on the timeline** you want to render (`Ctrl + A` or Shift-select).
3. Shift + Right-click one of the parts -> **Render in Place > Render Settings**:
   - **Mode:** *As Block Events* (or *As Separate Events*)
   - **Processing:** *Complete Signal Path*
   - **Tail Size:** *3 to 5 Seconds* (for reverb/delay tails)
   - **Bit Depth:** Match project (24-bit recommended)
   - **Mixdown to one audio file:** *Must be UNCHECKED*
   - **Source Tracks:** *Mute Source Events*
4. Click **Render**.
5. Move the new rendered tracks together, remove/hide the old tracks, and go to:  
   **File → Export → DAWproject**.

#### Step B: Convert to Logic Pro
1. Open **`DAW-Logic-Bridge.exe`**.
2. Choose **Cubase / DAWproject → Logic Pro (.logicx)**.
3. **Input:** Select your exported `.dawproject` file.
4. Click **START CONVERSION**.
5. **IMPORTANT FOR MAC TRANSFER:**  
   Logic sessions are folder packages. You **must zip the folder** before transferring:
   - Right-click the newly generated `YourSong.logicx` folder.
   - Choose **Compress to ZIP file** (Windows 11) or **Send to → Compressed folder** (Windows 10 / 7-Zip).
6. Send the zipped `YourSong.logicx.zip` file to your Mac client. Done!

---

## What Converts

| Feature | Support Level | Notes |
| :--- | :--- | :--- |
| **Audio Regions & Waveforms** | **100% Lossless** | Sample-accurate timeline placement, discrete cuts preserved |
| **Track Names & Ordering** | **100% Match** | Dynamic channel mapping matching arrange order |
| **Timeline Placement** | **100% Match** | Exact beat and tick positioning |
| **Mute States** | **100% Preserved** | Individual clip enable/mute flags respected |
| **Tempo & Time Signatures** | **100% Preserved** | BPM and meter maps transferred |
| **Sample Rate** | **Automatic** | Initializes audio engine to match source session (44.1k, 48k, etc.) |
| **Volume Automation** | Sidecar JSON | Exported to `Media/daw2logic Import/automation/` |
| **EQ (DAWproject Equalizer)** | Sidecar JSON | Exported to `Media/daw2logic Import/eq/` |
| **VST / AU Plugins** | ❌ Incompatible | Logic strictly uses AU; Cubase uses VST3. Bake before export! |

---

## Command Line Usage (CLI)

For automated server scripts, WSL, or headless environments:

### Convert DAWproject → Logic Pro:
```bash
daw2logic song.dawproject -o song.logicx
daw2logic song.dawproject -o song.logicx --force   # overwrite existing

Convert Logic Pro → DAWproject:
code
Bash
python logic2daw.pyong.logicx -o song.dawproject

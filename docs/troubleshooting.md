# Troubleshooting

## The meeting app does not hear the filtered voice

1. In Tapis, the **output device** must be **CABLE Input (VB-Audio Virtual Cable)**, and the
   filter must be running (the status bar says *Running*).
2. In the meeting app (Teams, Meet, Zoom, Discord, TeamTalk, OBS…), the **microphone** must be
   **CABLE Output (VB-Audio Virtual Cable)**. Input and output names are swapped on purpose: the
   app writes into the cable's input, the meeting app reads from its output.
3. Browser apps such as Google Meet: pick the microphone in the meeting's settings, and make sure
   the browser has microphone permission.

## There is no "CABLE Input" device

VB-CABLE is not installed. Run the Tapis installer again (it installs VB-CABLE when it is
missing) and restart Windows if the installer asks. When running from source, install VB-CABLE from
[vb-cable.com](https://www.vb-cable.com).

## Start does not work: the microphone is blocked

Tapis now says why and offers a button to the right Windows page. The usual causes:

1. **Windows privacy.** Settings › Privacy & security › Microphone has three switches:
   *Microphone access*, *Let apps access your microphone* and, further down,
   *Let desktop apps access your microphone*. Tapis is a desktop app, so it never appears in the
   list of apps on that page: only the last switch counts for it.
2. **Mute key or the laptop maker's app.** Many laptops have a microphone key (often F4 or F8,
   with a light) or a privacy switch in Lenovo Vantage, HP or Dell software. Windows then sends
   only silence, and Tapis warns that the microphone "only sends silence".
3. **Antivirus microphone protection** (Kaspersky, ESET, Bitdefender, Norton…) or a policy on a
   school or office PC. Allow Tapis there.
4. **Another app holds the microphone exclusively.** Close it, or turn off *Allow applications to
   take exclusive control of this device* in the microphone's properties (Sound settings › More
   sound settings › Recording › Properties › Advanced).

If *Exclusive mode* is ticked in Tapis and the device refuses it, Tapis falls back to shared mode
by itself.

## "Record noise" or sending a sample fails

- **Record noise** only needs the microphone (not VB-CABLE). If it says the microphone only sent
  silence, see the section above.
- When sending fails, the message says why: no internet, a slow connection, or a **school or
  office network that blocks the sample server**. In that case try another network, for example a
  phone hotspot. "Show Details" in the message has the technical reason for a bug report.

## The sound crackles or drops out

- Look at **xruns** in the status bar. If the number keeps climbing, the audio is starved.
- Turn off **Exclusive mode** if it is on, or try it if it is off; some devices prefer one or the other.
- Close other apps that use the same microphone in exclusive mode.
- Use the **C++ engine** (the status bar says *Engine: C++*). The installer always includes it.
- The AI denoiser costs more CPU than the spectral one; switch to *Spectral* on a slow PC.

## My voice sounds thin, robotic, dry or cut off

- Turn on **Vocal / singing mode**. It keeps the harmonics and natural decay of the voice,
  especially on long sung notes. [How it compares](images/vocal-compare.png).
- Lower **Mix** to 70-85 % to blend some of the original sound back in.
- Lower **Strength** (1.0 is the default; 0.6-0.8 keeps more of the voice).
- Lower the **Gate threshold** or turn the gate off; a high gate cuts quiet syllables.
- Click **Learn my room noise** while you stay quiet, so the spectral denoiser knows the real noise.
- Check the **Equalizer**: a strong high-pass or several stacked presets can remove too much.

## Windows SmartScreen warns about the installer

The installer is not code-signed yet, so Windows may show *Windows protected your PC*. Choose
**More info › Run anyway** if you downloaded it from the
[official releases page](https://github.com/SkillsHUB-Electronics/tapis/releases).

## Reset all settings

Quit Tapis from the tray menu, then delete `%APPDATA%\Tapis\config.json`. The next
start uses the defaults.

## Still stuck?

Open a [bug report](https://github.com/SkillsHUB-Electronics/tapis/issues/new?template=bug_report.yml)
with the Tapis version (Settings › About), your Windows version, the devices you use and
what the status bar shows. The output of `tapisctl status` helps a lot.

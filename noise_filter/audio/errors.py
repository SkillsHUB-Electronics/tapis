"""Turn audio engine errors into something a user can act on.

Both engines report Windows audio errors as text: the C++ WASAPI engine as
"input: IAudioClient::Initialize (shared) failed (HRESULT 0x80070005)", PortAudio (sounddevice) as
"... [Windows WASAPI error -2147024891]". `classify` maps them to a reason key (translated in the
UI as `mic.err.<reason>`) and says which Windows settings page helps.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# HRESULT -> reason
_CODES = {
    0x80070005: "denied",            # E_ACCESSDENIED: privacy settings, antivirus, company policy
    0x8889000A: "in_use",            # AUDCLNT_E_DEVICE_IN_USE: another app holds it exclusively
    0x8889000E: "exclusive_off",     # AUDCLNT_E_EXCLUSIVE_MODE_NOT_ALLOWED
    0x88890004: "not_found",         # AUDCLNT_E_DEVICE_INVALIDATED: unplugged / disabled
    0x80070490: "not_found",         # E_NOTFOUND: saved device no longer exists
    0x88890008: "format",            # AUDCLNT_E_UNSUPPORTED_FORMAT
    0x88890019: "format",            # AUDCLNT_E_BUFFER_SIZE_NOT_ALIGNED (exclusive)
    0x88890020: "format",            # AUDCLNT_E_INVALID_DEVICE_PERIOD
    0x8889001E: "busy",              # AUDCLNT_E_RESOURCES_INVALIDATED
    0x88890026: "busy",              # AUDCLNT_E_ENDPOINT_OFFLOAD_NOT_CAPABLE
    0x88890003: "busy",              # AUDCLNT_E_WRONG_ENDPOINT_TYPE
    0x8889000F: "busy",              # AUDCLNT_E_ENDPOINT_CREATE_FAILED
    0x88890017: "busy",              # AUDCLNT_E_CPUUSAGE_EXCEEDED
}

PRIVACY_URL = "ms-settings:privacy-microphone"
SOUND_URL = "ms-settings:sound"


@dataclass
class AudioError:
    reason: str            # denied | in_use | exclusive_off | not_found | format | busy | silent | unknown
    side: str              # "input", "output" or "" when unknown
    detail: str            # the original message, for bug reports

    @property
    def settings_url(self) -> str:
        if self.reason in ("denied", "silent"):
            return PRIVACY_URL
        return SOUND_URL if self.reason != "unknown" else ""


def hresult(msg: str) -> int | None:
    m = re.search(r"HRESULT 0x([0-9A-Fa-f]{8})", msg)
    if m:
        return int(m.group(1), 16)
    m = re.search(r"(?:WASAPI|Windows) error (-?\d+)", msg)        # PortAudio prints it signed
    if m:
        return int(m.group(1)) & 0xFFFFFFFF
    return None


def classify(e: BaseException | str) -> AudioError:
    msg = str(e)
    low = msg.lower()
    side = "input" if low.startswith("input") or "inputstream" in low else (
        "output" if low.startswith("output") or "outputstream" in low else "")
    code = hresult(msg)
    reason = _CODES.get(code, "") if code is not None else ""
    if not reason:
        if "access" in low and "denied" in low:
            reason = "denied"
        elif "48 khz" in low or "invalid sample rate" in low or "unsupported format" in low:
            reason = "format"
        elif "device unavailable" in low or "invalid device" in low or "no such device" in low:
            reason = "not_found"
        else:
            reason = "unknown"
    return AudioError(reason, side, msg)


def is_silent(level_db: float) -> bool:
    """Digital silence (all samples exactly 0). A real microphone, even a quiet one, has a noise
    floor far above this; Windows feeds exact zeros when it blocks or mutes the microphone."""
    return level_db < -140.0

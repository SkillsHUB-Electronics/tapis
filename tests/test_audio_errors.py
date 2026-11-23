"""Audio device errors are turned into reasons the app can explain (privacy block, device in use...)."""
from noise_filter.audio import errors


def test_native_engine_messages():
    e = errors.classify("input: IAudioClient::Initialize (shared) failed (HRESULT 0x80070005)")
    assert (e.reason, e.side, e.settings_url) == ("denied", "input", errors.PRIVACY_URL)
    e = errors.classify("output: open device failed (HRESULT 0x80070490)")
    assert (e.reason, e.side, e.settings_url) == ("not_found", "output", errors.SOUND_URL)
    assert errors.classify("input: IAudioClient::Initialize (exclusive) failed (HRESULT 0x8889000A)").reason == "in_use"
    assert errors.classify("input: IAudioClient::Initialize (exclusive) failed (HRESULT 0x8889000E)").reason == "exclusive_off"
    assert errors.classify("input: device does not support 48 kHz in exclusive mode").reason == "format"


def test_portaudio_messages():
    msg = ("input: Error opening InputStream: Unanticipated host error [PaErrorCode -9999]: "
           "'Undefined external error.' [Windows WASAPI error -2147024891]")
    e = errors.classify(msg)
    assert (e.reason, e.side) == ("denied", "input") and e.detail == msg
    assert errors.classify("output: Error opening OutputStream: [Windows WASAPI error -2004287478]").reason == "in_use"
    assert errors.classify("Error opening InputStream: Invalid sample rate [PaErrorCode -9997]").reason == "format"
    e = errors.classify(RuntimeError("something odd"))
    assert (e.reason, e.settings_url) == ("unknown", "")


def test_silence_detector():
    assert errors.is_silent(-180.0)              # exact zeros (analyzer floor)
    assert not errors.is_silent(-95.0)           # a quiet but real microphone


def test_every_reason_is_translated():
    import json
    from importlib import resources
    for lang in ("en", "id"):
        d = json.loads(resources.files("noise_filter.i18n").joinpath(f"{lang}.json").read_text("utf-8"))
        for r in ("denied", "silent", "in_use", "exclusive_off", "not_found", "format", "busy", "unknown"):
            assert f"mic.err.{r}" in d and f"mic.short.{r}" in d
            d[f"mic.err.{r}"].format(side="x"); d[f"mic.short.{r}"].format(side="x")
        from noise_filter import net
        for r in net.REASONS:
            assert f"contrib.err.{r}" in d

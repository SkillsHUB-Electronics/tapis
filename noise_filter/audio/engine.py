"""Realtime engine: input device -> Pipeline -> output device (e.g. VB-Cable).

Uses two callback streams (input and output can be different devices) joined by a
tiny lock-free-ish ring buffer. Keep the target fill at ~1 frame for low latency.
"""
import threading
import numpy as np
from ..core import Pipeline, FRAME_SIZE, SAMPLE_RATE


class Ring:
    def __init__(self, cap=FRAME_SIZE * 16):
        self.buf = np.zeros(cap, np.float32)
        self.cap, self.r, self.w, self.lock = cap, 0, 0, threading.Lock()

    def available(self): return self.w - self.r

    def write(self, x):
        with self.lock:
            for s in (x,):
                idx = (self.w + np.arange(len(s))) % self.cap
                self.buf[idx] = s
                self.w += len(s)
            if self.w - self.r > self.cap:       # overflow: drop oldest
                self.r = self.w - self.cap

    def read(self, n):
        with self.lock:
            if self.w - self.r < n:
                return None
            idx = (self.r + np.arange(n)) % self.cap
            self.r += n
            return self.buf[idx].copy()


NO_OUTPUT = "nf:none"


def _wasapi_settings(sd, device, exclusive: bool):
    """Exclusive mode, or shared mode with Windows' sample rate converter on (most laptop
    microphones run at 44.1 or 16 kHz natively and would otherwise refuse 48 kHz)."""
    try:
        api = sd.query_hostapis(sd.query_devices(device)["hostapi"])["name"]
    except Exception:
        return None
    if api != "Windows WASAPI":
        return None
    if exclusive:
        return sd.WasapiSettings(exclusive=True)
    try:
        return sd.WasapiSettings(auto_convert=True)     # sounddevice >= 0.4.6
    except TypeError:
        return None


class Engine:
    def __init__(self, pipeline: Pipeline, in_dev: int, out_dev, exclusive: bool = False):
        """out_dev None/NO_OUTPUT: record only (the processed audio is discarded)."""
        import sounddevice as sd
        self.sd, self.pipe = sd, pipeline
        self.inring, self.outring = Ring(), Ring()
        kw = dict(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=FRAME_SIZE, latency="low")
        try:
            self.stream_in = sd.InputStream(device=in_dev, callback=self._in_cb,
                                            extra_settings=_wasapi_settings(sd, in_dev, exclusive), **kw)
        except Exception as e:
            raise RuntimeError(f"input: {e}") from e
        self.stream_out = None
        if out_dev is not None and out_dev != NO_OUTPUT:
            try:
                self.stream_out = sd.OutputStream(device=out_dev, callback=self._out_cb,
                                                  extra_settings=_wasapi_settings(sd, out_dev, exclusive), **kw)
            except Exception as e:
                self.stream_in.close()
                raise RuntimeError(f"output: {e}") from e
        self.xruns = 0

    def _in_cb(self, indata, frames, t, status):
        if status: self.xruns += 1
        self.inring.write(indata[:, 0])
        while (f := self.inring.read(FRAME_SIZE)) is not None:
            y = self.pipe.process(f)
            if self.stream_out is not None:
                self.outring.write(y)

    def _out_cb(self, outdata, frames, t, status):
        if status: self.xruns += 1
        f = self.outring.read(frames)
        outdata[:, 0] = f if f is not None else 0.0

    def start(self):
        try:
            self.stream_in.start()
        except Exception as e:
            raise RuntimeError(f"input: {e}") from e
        if self.stream_out is not None:
            try:
                self.stream_out.start()
            except Exception as e:
                self.stream_in.stop()
                raise RuntimeError(f"output: {e}") from e

    def stop(self):
        for s in (self.stream_in, self.stream_out):
            if s is not None:
                try:
                    s.stop(); s.close()
                except Exception:
                    pass

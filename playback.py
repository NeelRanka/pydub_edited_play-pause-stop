"""
Support for playing AudioSegments. Pyaudio will be used if it's installed,
otherwise will fallback to ffplay. Pyaudio is a *much* nicer solution, but
is tricky to install. See my notes on installing pyaudio in a virtualenv (on
OSX 10.10): https://gist.github.com/jiaaro/9767512210a1d80a8a0d
"""

import subprocess
from tempfile import NamedTemporaryFile
from .utils import get_player_name, make_chunks
import threading
import sys

PLAYER = get_player_name()
play_flag=1


def _play_with_ffplay(seg):
    print("in ffplay")
    with NamedTemporaryFile("w+b", suffix=".wav") as f:
        seg.export(f.name, "wav")
        subprocess.call([PLAYER, "-nodisp", "-autoexit", "-hide_banner", f.name])


def _play_with_pyaudio(seg):
    import pyaudio
    global play_flag
    print("in pyaudio")
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(seg.sample_width),
                    channels=seg.channels,
                    rate=seg.frame_rate,
                    output=True)
    # break audio into half-second chunks (to allows keyboard interrupts)
    for chunk in make_chunks(seg,500):
        stream.write(chunk._data)
        if play_flag==2:
            break
        elif play_flag==0:
            while play_flag==0:
                continue


    stream.stop_stream()
    stream.close()

    p.terminate()

def check_play_pause(t1):
    global play_flag
    play_flag=1
    while t1.is_alive():
        x=input("space+Enter to play/pause and e+Enter to stop ")
        if x=='e':
            play_flag=2
            break
        else:
            if play_flag==0:
                play_flag=1
            elif play_flag==1:
                play_flag=0


def _play_with_simpleaudio(seg):
    import simpleaudio
    print("in simpleaudio")
    return simpleaudio.play_buffer(
        seg.raw_data, 
        num_channels=seg.channels, 
        bytes_per_sample=seg.sample_width, 
        sample_rate=seg.frame_rate
    )

def kill(self):
    self._running=False

def play(audio_segment):
    print("in play")
    try:
        playback = _play_with_simpleaudio(audio_segment)
        try:
            print("\n\nplaying\n\n")
            playback.wait_done()
        except KeyboardInterrupt:
            playback.stop()
    except ImportError:
        pass
    else:
        return
    
    try:
        t1=threading.Thread(target=_play_with_pyaudio,args=(audio_segment,))
        t2=threading.Thread(target=check_play_pause,args=(t1,))
        t1.start()
        t2.start()
       
        t1.join()
        t2.join()
        #_play_with_pyaudio(audio_segment)
        return
    except ImportError:
        pass
    else:
        return
    
    _play_with_ffplay(audio_segment)

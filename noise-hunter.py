'''
    Noise Hunter by @sha0coder

        - apply frequency filters (bandpass)
        - apply frequency exclusions to remove ranges
        - apply dbs filtesr
        - apply dbs exclussions
        - target: hunt the noise and display the wave


    TODO:
         - store a json with metrics
         - do a white noise specific for those freqs
'''

import os
import time
import math
import csv
import queue
import argparse
import threading
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.io.wavfile import write
from scipy.signal import spectrogram
from scipy.signal import butter, lfilter

fs = 44100
max_freq = None
min_freq = None
duration = 60
min_db = -30
max_db = -20
cutoff_freq_down = 300
cutoff_freq_up = 2000
male_min = 85 # Hz
male_max = 180 # Hz
female_min = 165 #Hz
female_max = 255 # Hz
chunk = 2048
audio_q = queue.Queue(maxsize=10)
window_size = 1024
buffer = np.zeros(window_size)
args = None
mic_callibration = -42 # dBV/Pa (aprox.)
metrics = []
low_voice = 80 # Hz
high_voice = 4000 # Hz

known_freqs = {
    27.50: "music, A0",
    29.14: "music, A#0/Bb0",
    30.87: "music, B0",
    32.70: "music, C1",
    34.65: "music, C#1/Db1",
    36.71: "music, D1",
    38.89: "music, D#1/Eb1",
    41.20: "music, E1",
    43.65: "music, F1",
    46.25: "music, F#1/Gb1",
    49.00: "music, G1",
    51.91: "music, G#1/Ab1",
    55.00: "music, A1",
    58.27: "music, A#1/Bb1",
    61.74: "music, B1",
    65.41: "music, C2",
    69.30: "music, C#2/Db2",
    73.42: "music, D2",
    77.78: "music, D#2/Eb2",
    82.41: "music, E2",
    87.31: "music, F2",
    92.50: "music, F#2/Gb2",
    98.00: "music, G2",
    103.83: "music, G#2/Ab2",
    110.00: "music, A2",
    116.54: "music, A#2/Bb2",
    123.47: "music, B2",
    130.81: "music, C3",
    138.59: "music, C#3/Db3",
    146.83: "music, D3",
    155.56: "music, D#3/Eb3",
    164.81: "music, E3",
    174.61: "music, F3",
    185.00: "music, F#3/Gb3",
    196.00: "music, G3",
    207.65: "music, G#3/Ab3",
    220.00: "music, A3",
    233.08: "music, A#3/Bb3",
    246.94: "music, B3",
    261.63: "music, C4 (Middle C)",
    277.18: "music, C#4/Db4",
    293.66: "music, D4",
    311.13: "music, D#4/Eb4",
    329.63: "music, E4",
    349.23: "music, F4",
    369.99: "music, F#4/Gb4",
    392.00: "music, G4",
    415.30: "music, G#4/Ab4",
    440.00: "music, A4 (instrument tunning)",
    466.16: "music, A#4/Bb4",
    493.88: "music, B4",
    523.25: "music, C5",
    554.37: "music, C#5/Db5",
    587.33: "music, D5",
    622.25: "music, D#5/Eb5",
    659.25: "music, E5",
    698.46: "music, F5",
    739.99: "music, F#5/Gb5",
    783.99: "music, G5",
    830.61: "music, G#5/Ab5",
    880.00: "music, A5",
    932.33: "music, A#5/Bb5",
    987.77: "music, B5",
    1046.50: "music, C6",
    1108.73: "music, C#6/Db6",
    1174.66: "music, D6",
    1244.51: "music, D#6/Eb6",
    1318.51: "music, E6",
    1396.91: "music, F6",
    1479.98: "music, F#6/Gb6",
    1567.98: "music, G6",
    1661.22: "music, G#6/Ab6",
    1760.00: "music, A6",
    1864.66: "music, A#6/Bb6",
    1975.53: "music, B6",
    2093.00: "music, C7",
    2217.46: "music, C#7/Db7",
    2349.32: "music, D7",
    2489.02: "music, D#7/Eb7",
    2637.02: "music, E7",
    2793.83: "music, F7",
    2959.96: "music, F#7/Gb7",
    3135.96: "music, G7",
    3322.44: "music, G#7/Ab7",
    3520.00: "music, A7",
    3729.31: "music, A#7/Bb7",
    3951.07: "music, B7",
    4186.01: "music, C8"
}


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs):
    b, a = butter_lowpass(cutoff, fs)
    return lfilter(b, a, data)

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def highpass_filter(data, cutoff, fs):
    b, a = butter_highpass(cutoff, fs)
    return lfilter(b, a, data)

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band', analog=False)
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return lfilter(b, a, data)

def db_to_amp(db):
    return 10**(db / 20)

def amp_to_db(amp, eps=1e-12):
    return 20 * np.log10(max(amp, eps))

def amp_to_db_prev(amp):
    return 20 * math.log10(amp)

min_amp = db_to_amp(min_db)
max_amp = db_to_amp(max_db)

recorded = []

def hook(indata, frames, time, status):
    if status:
        print(status)
    audio = indata[:, 0].copy()

    freqs = np.fft.rfftfreq(len(audio), 1/fs)
    spectrum = np.abs(np.fft.rfft(audio))
    freq = round(freqs[np.argmax(spectrum)], 2)

    # discard freq zero, it's not exactly silence silence should be amp zero.
    if freq == 0:
        return

    # apply min freq filters
    if args.fl and freq < args.fl:
        return

    # apply max freq filter
    if args.fh and freq > args.fh:
        return
    
    # apply freq sub-ranges exclusion
    if args.efl and args.efh and args.efl <= freq and  freq <= args.efh:
        return

    # do the band pass if there are min freq and max freq to get well the amplitude
    if args.fl and args.fh:
        if args.fl == args.fh:
            args.fl -= 10
            args.fh += 10
        audio = bandpass_filter(audio, args.fl, args.fh, fs, order=5)

    rms = round(float(np.sqrt(np.mean(audio**2))), 4)
    amp = np.max(np.abs(audio))
    max_amp = round(float(np.max(audio)), 4)
    min_amp = round(float(np.min(audio)), 4)
    dbs = round(amp_to_db(amp))

    # check pressure level for warning the user
    V_per_Pa = 10**(mic_callibration/20)  # factor lineal
    pressure_rms = rms / V_per_Pa  # si 1.0 digital = 1 VFS
    dB_SPL = round(float(20 * np.log10(pressure_rms / 20e-6)), 2)



    # discard silence
    if amp == 0:
        return

    # min decibels filter
    if args.dl and dbs < args.dl:
        return

    # max decibles filter
    if args.dh and dbs > args.dh:
        return

    # register max freq
    global max_freq
    if not max_freq or max_freq < freq:
        max_freq = freq

    # register min freq
    global min_freq
    if not min_freq or freq < min_freq:
        min_freq = freq


    # learn noise
    '''
    global daily_noise
    if freq not in daily_noise:
        daily_noise.update({freq: set()})
    daily_noise[freq].add(dbs)
    '''
        
    # discard daily learnt noise
    '''
    if freq in noise_learned:
        if dbs in noise_learned[freq]:
            return
    '''

    # it could be voice, also couldn't
    voice = freq >= low_voice and freq <= high_voice

    # presure damage alerts
    tag = ''
    if not voice:
        if dbs >= -3 and dbs <= -2:
            tag = 'WARNING HIGH DECIBEL '
        elif dbs > -2 and dbs <= 0:
            tag = 'ALERT HIGH SIGNAL '
        elif dbs == 0:
            tag = 'ALERT VERY HIGH SIGNAL!!!!! '
        elif dbs > 50:
            tag = 'far '
    elif dbs > 50:
        tag = 'far voice?'

    # fingerprint common sonunds
    if freq in known_freqs:
        tag += known_freqs[freq]
    elif freq < 20:
        tag += 'non audible utra low'
    elif freq > 20000:
        tag += 'non audible'
    elif freq > 18000:
        tag += 'only audible in young ears'
    elif freq == 115:
        tag += 'engine'

    if args.tag and not tag:
        return

    # otherwise we hunted a sound:
    print(f'detected {freq}Hz {dbs}dBFS {dB_SPL}dBSPL rms:{rms} amp range:[{min_amp}, {max_amp}]  {tag}')

    if args.save_csv:
        metrics.append({
            'freq': freq,
            'dbfs': dbs,
            'dbspl': dB_SPL,
            'rms': rms,
            'min_amp': min_amp,
            'max_amp': max_amp,
            'tag': tag,
        })

    if args.plot:
        try:
            audio_q.put_nowait(audio)
        except queue.Full:
            pass

    if args.out:
        recorded.append(audio.copy())


def plot_consumer():
    plt.ion()
    fig, ax = plt.subplots()
    line, = ax.plot(np.zeros(1024))
    plt.show(block=False)

    while True:
        audio = audio_q.get()
        x = range(len(audio))
        line.set_xdata(x)
        line.set_ydata(audio)
        ax.set_xlim(0, len(audio))
        ax.set_ylim(audio.min(), audio.max())
        fig.canvas.draw()
        fig.canvas.flush_events()
        #plt.pause(0.001)


def main():
    global args
    parser = argparse.ArgumentParser()
    #parser.add_argument('-f', type=float, default=0, help='filter by frequency in Hz, ie -f 255')
    #parser.add_argument('-d', type=int, default=0, help='filter by decibels, ie: -d 30  this is -30dB')
    parser.add_argument('-fl', type=float, default=0, help='bandpass lowcut and filter by frequency range, ie: -fl 100 -fh 300')
    parser.add_argument('-fh', type=float, default=0, help='bandpass highcut and filter by frequency range, ie: -fl 100 -fh 300')
    parser.add_argument('-efl', type=float, default=0, help='exclude frequency range, ie: -efl 1 -efh 100.01')
    parser.add_argument('-efh', type=float, default=0, help='exclude by frequency range, ie: -efl 1 -efh 100.01')
    parser.add_argument('-dl', type=int, default=0, help='filter by decibels range, ie: -dl -30 -dh -20')
    parser.add_argument('-dh', type=int, default=0, help='filter by decibels range, ie: -dl -30 -dh -20')
    #parser.add_argument('-edl', type=int, default=0, help='exclude by decibels range, ie: -efl 100 -fh 50  (note that less is more because is negative)')
    #parser.add_argument('-edh', type=int, default=0, help='exclude by decibels range, ie: -efl 100 -fh 50  (note that less is more because is negative)')
    parser.add_argument('-p', '--plot', default=False, action='store_true', help='Draw a plot to see the wave')
    parser.add_argument('--save-csv', type=str, default=None, help='save metrics in csv:  --save-csv file.csv  ')
    parser.add_argument('-o', '--out', type=str, default=None, help='save filtered noise to wav when control+C is pressed:  -o file.wav  ')
    parser.add_argument('-w', '--white', default=False, action='store_true', help='create white noise in loop, must be combined with a freq filter')
    parser.add_argument('-t', '--tag', default=False, action='store_true', help='discard all the noises with no tag classification')

    args = parser.parse_args()

    if args.white: 
        input('adjust the speakers volume and press enter to start with white noise from {args.fl}Hz to {args.fh}Hz.')
        while True:
            samples = int(1024 * fs)
            white_noise = np.random.normal(0, 1, samples)
            band_limited_noise = bandpass_filter(white_noise, args.fl, args.fh, fs)
            sd.play(band_limited_noise, samplerate=fs)
            sd.wait()



    if args.plot:
        threading.Thread(target=plot_consumer, daemon=True).start()

    while True:
        recorded = []

        with sd.InputStream(channels=1, samplerate=fs, callback=hook):
            sd.sleep(duration * 1000)
        #with sd.InputStream(channels=1, samplerate=fs, callback=hook, blocksize=chunk):
        #    sd.sleep(duration * 1000)

        if not recorded:
            continue

        '''
        print('generating sample...')
        data = np.concatenate(recorded)
        write("sample.wav", fs, (data * 32767).astype(np.int16))
        os.popen('sox sample.wav -n spectrogram -x 4096 -y 1024 -X 100 -o sample.png').close()
        os.popen("feh sample.png").close()
        '''


try:
    main()
except KeyboardInterrupt:
    print(f'freq range: {min_freq} - {max_freq}')
    if args.save_csv:
        with open(args.save_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)
    if args.out:
        data = np.concatenate(recorded)
        write(args.out, fs, (data * 32767).astype(np.int16))     




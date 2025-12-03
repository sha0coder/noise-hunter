

# Noise Hunter

```bash
❯❯❯ python3 noise-hunter.py --help
usage: noise-hunter.py [-h] [-fl FL] [-fh FH] [-efl EFL] [-efh EFH] [-dl DL]
                       [-dh DH] [-p] [-o OUT] [-w]

options:
  -h, --help     show this help message and exit
  -fl FL         bandpass lowcut and filter by frequency range, ie: -fl 100 -fh
                 300
  -fh FH         bandpass highcut and filter by frequency range, ie: -fl 100 -fh
                 300
  -efl EFL       exclude frequency range, ie: -efl 1 -efh 100.01
  -efh EFH       exclude by frequency range, ie: -efl 1 -efh 100.01
  -dl DL         filter by decibels range, ie: -fl 30 -fh 20 (note that less is
                 more because is negative)
  -dh DH         filter by decibels range, ie: -fl 30 -fh 20 (note that less is
                 more because is negative)
  -p, --plot     Draw a plot to see the wave
  -o, --out OUT  save filtered noise to wav: -o file.wav
  -w, --white    create white noise in loop, must be combined with a freq filter
```

## Examples

```
❯❯❯ python3 noise-hunter.py
detected 115.14Hz -55dBs rms:0.0007 amp range:[-0.0018, 0.0013]
detected 115.14Hz -54dBs rms:0.0006 amp range:[-0.0012, 0.002]
detected 230.29Hz -53dBs rms:0.0008 amp range:[-0.0023, 0.0023]
detected 345.43Hz -52dBs rms:0.0007 amp range:[-0.0025, 0.0024]
detected 115.14Hz -54dBs rms:0.0007 amp range:[-0.0019, 0.0021]
detected 230.29Hz -52dBs rms:0.0008 amp range:[-0.0024, 0.0023]
detected 230.29Hz -50dBs rms:0.001 amp range:[-0.0033, 0.0021]
detected 234.57Hz -50dBs rms:0.001 amp range:[-0.0028, 0.0031]
detected 115.14Hz -51dBs rms:0.001 amp range:[-0.0028, 0.0028]
detected 115.14Hz -50dBs rms:0.0011 amp range:[-0.0026, 0.003]
detected 501.14Hz -50dBs rms:0.0013 amp range:[-0.0029, 0.0031]
detected 689.06Hz -53dBs rms:0.0008 amp range:[-0.0016, 0.0023]
detected 128.95Hz -47dBs rms:0.0014 amp range:[-0.0046, 0.0034]
detected 115.14Hz -48dBs rms:0.0014 amp range:[-0.004, 0.0037]
detected 1002.27Hz -54dBs rms:0.0009 amp range:[-0.002, 0.0021]
detected 115.14Hz -48dBs rms:0.0013 amp range:[-0.0042, 0.0041]
```

```bash
❯❯❯ python3 noise-hunter.py -fl 200 -fh 1000 -p -o file.wav
```
<img src=pics/pic.png width=100%>


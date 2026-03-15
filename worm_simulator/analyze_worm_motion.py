import json
import os
import numpy as np
import matplotlib.pyplot as plt

# automatically detect newest output folder
BASE_OUTPUT = r"D:\Project worm\openworm\output"

folders = [
    os.path.join(BASE_OUTPUT, f)
    for f in os.listdir(BASE_OUTPUT)
    if os.path.isdir(os.path.join(BASE_OUTPUT, f))
]

folders.sort(key=os.path.getmtime)

latest = folders[-1]

FILE_PATH = os.path.join(latest, "worm_motion_log.wcon")

print("Analyzing:", FILE_PATH)

with open(FILE_PATH, "r") as f:
    data = json.load(f)

worm = data["data"][0]

# convert to numpy arrays
x = np.array(worm["x"])
y = np.array(worm["y"])
t = np.array(worm["t"])

# calculate worm center position
center_x = x.mean(axis=1)
center_y = y.mean(axis=1)

# calculate speed
dx = np.diff(center_x)
dy = np.diff(center_y)
dt = np.diff(t)

speed = np.sqrt(dx**2 + dy**2) / dt

# ---- BODY CURVATURE ----

dx_seg = np.gradient(x, axis=1)
dy_seg = np.gradient(y, axis=1)

ddx_seg = np.gradient(dx_seg, axis=1)
ddy_seg = np.gradient(dy_seg, axis=1)

curvature = np.abs(dx_seg * ddy_seg - dy_seg * ddx_seg) / (dx_seg**2 + dy_seg**2)**1.5
mean_curvature = curvature.mean(axis=1)

# ---- OSCILLATION FREQUENCY ----

signal = x.mean(axis=0)
fft = np.fft.rfft(signal)
freqs = np.fft.rfftfreq(len(signal), d=(t[1] - t[0]))

dominant_freq = freqs[np.argmax(np.abs(fft))]

# ---- SAVE PLOTS ----

speed_path = os.path.join(latest, "speed_vs_time.png")
curvature_path = os.path.join(latest, "body_curvature.png")
trajectory_path = os.path.join(latest, "worm_trajectory.png")

# trajectory
plt.figure(figsize=(6,6))
plt.plot(center_x, center_y)
plt.title("Worm Center Trajectory")
plt.xlabel("X position")
plt.ylabel("Y position")
plt.savefig(trajectory_path)
plt.close()

# speed vs time
plt.figure(figsize=(6,4))
plt.plot(t[:-1], speed)
plt.title("Speed vs Time")
plt.xlabel("Time")
plt.ylabel("Speed")
plt.savefig(speed_path)
plt.close()

# curvature
plt.figure(figsize=(6,4))
plt.plot(t, mean_curvature)
plt.title("Body Curvature Over Time")
plt.xlabel("Time")
plt.ylabel("Curvature")
plt.savefig(curvature_path)
plt.close()

# save frequency
freq_file = os.path.join(latest, "oscillation_frequency.txt")
with open(freq_file, "w") as f:
    f.write(f"Dominant Oscillation Frequency: {dominant_freq:.4f} Hz")

print("Saved:")
print(speed_path)
print(curvature_path)
print(freq_file)

# ---- CLEANUP OLD RUNS (keep last 5) ----

import shutil

if len(folders) > 5:
    old = folders[:-5]
    for f in old:
        print("Deleting old run:", f)
        shutil.rmtree(f)
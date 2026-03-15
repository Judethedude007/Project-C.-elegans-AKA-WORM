import json
import numpy as np
import matplotlib.pyplot as plt

FILE_PATH = r"D:\Project worm\openworm\output\C2_FW_2026-03-15_10-02-09\worm_motion_log.wcon"

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

# plot trajectory
plt.figure(figsize=(6,6))
plt.plot(center_x, center_y)
plt.title("Worm Center Trajectory")
plt.xlabel("X position")
plt.ylabel("Y position")
plt.show()

# plot speed
plt.figure(figsize=(6,4))
plt.plot(t[:-1], speed)
plt.title("Worm Speed Over Time")
plt.xlabel("Time")
plt.ylabel("Speed")
plt.show()
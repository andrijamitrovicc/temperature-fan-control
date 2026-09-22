import tkinter as tk
from tkinter import ttk
import serial
import threading
import time
from collections import deque

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# =========================
# SERIAL
# =========================

ser = None
COM_PORT = "COM24"
BAUDRATE = 115200

# =========================
# GLOBAL
# =========================

temperatura = 0.0
arduino_prag = 0
fan_state = 0
rezim = 0

python_prag = 30.0

# =========================
# DATA
# =========================

MAX_POINTS = 200

x_data = deque(maxlen=MAX_POINTS)
temp_data = deque(maxlen=MAX_POINTS)
fan_data = deque(maxlen=MAX_POINTS)

start_time = time.time()

# =========================
# CONNECT SERIAL
# =========================

def connect_serial():
    global ser, COM_PORT

    COM_PORT = com_entry.get().strip()

    try:
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=1)
        status_label.config(text="Status: CONNECTED")
    except:
        ser = None
        status_label.config(text="Status: DISCONNECTED")

# =========================
# GUI
# =========================

root = tk.Tk()
root.title("IR Temperature Control")
root.geometry("1000x700")

header_frame = ttk.Frame(root)
header_frame.pack(fill="x", side="top")

header_label = tk.Label(
    header_frame,
    text="Dragan Forspreher 121/22 RI | Andrija Mitrovic 149/22 RI",
    font=("Arial", 10)
)
header_label.pack(side="right", padx=10, pady=2)

com_frame = ttk.Frame(root)
com_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(com_frame, text="COM Port:").pack(side="left")

com_entry = ttk.Entry(com_frame, width=10)
com_entry.insert(0, COM_PORT)
com_entry.pack(side="left", padx=5)

ttk.Button(
    com_frame,
    text="Connect",
    command=connect_serial
).pack(side="left", padx=5)

status_label = ttk.Label(
    com_frame,
    text="Status: DISCONNECTED"
)
status_label.pack(side="left", padx=10)

info_frame = ttk.Frame(root)
info_frame.pack(fill="x", padx=10, pady=10)

temp_label = ttk.Label(
    info_frame,
    text="Temperatura: -- °C",
    font=("Arial", 18)
)
temp_label.pack(anchor="w")

mode_label = ttk.Label(
    info_frame,
    text="Rezim: ---",
    font=("Arial", 14)
)
mode_label.pack(anchor="w")

fan_label = ttk.Label(
    info_frame,
    text="Ventilator: OFF",
    font=("Arial", 14)
)
fan_label.pack(anchor="w")

arduino_prag_label = ttk.Label(
    info_frame,
    text="Arduino prag: -- °C",
    font=("Arial", 14)
)
arduino_prag_label.pack(anchor="w")

# =========================
# PYTHON PRAG
# =========================

prag_frame = ttk.Frame(root)
prag_frame.pack(fill="x", padx=10)

ttk.Label(
    prag_frame,
    text="Python prag (°C):"
).pack(side="left")

python_prag_entry = ttk.Entry(
    prag_frame,
    width=10
)
python_prag_entry.insert(0, "30")
python_prag_entry.pack(side="left", padx=5)

def update_python_prag():
    global python_prag

    try:
        python_prag = float(
            python_prag_entry.get()
        )

        prag_status.config(
            text=f"Python prag: {python_prag:.1f} °C"
        )

    except:
        prag_status.config(
            text="Neispravan prag!"
        )

ttk.Button(
    prag_frame,
    text="Update Prag",
    command=update_python_prag
).pack(side="left", padx=5)

prag_status = ttk.Label(
    prag_frame,
    text="Python prag: 30.0 °C"
)
prag_status.pack(side="left", padx=10)
# =========================
# COMMANDS
# =========================

def send_command(cmd):
    global ser

    if ser:
        try:
            ser.write((cmd + "\n").encode())
        except:
            pass

def auto_arduino():
    send_command("A")

def override_on():
    send_command("ON")

def override_off():
    send_command("OFF")

def auto_python_mode():
    send_command("P")

# =========================
# BUTTONS
# =========================

btn_frame = ttk.Frame(root)
btn_frame.pack(fill="x", pady=10)

ttk.Button(
    btn_frame,
    text="AUTO Arduino",
    command=auto_arduino
).pack(side="left", padx=5)

ttk.Button(
    btn_frame,
    text="Override ON",
    command=override_on
).pack(side="left", padx=5)

ttk.Button(
    btn_frame,
    text="Override OFF",
    command=override_off
).pack(side="left", padx=5)

ttk.Button(
    btn_frame,
    text="AUTO Python",
    command=auto_python_mode
).pack(side="left", padx=5)

# =========================
# GRAPH
# =========================

fig = Figure(figsize=(8, 5), dpi=100)
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(
    fig,
    master=root
)

canvas.get_tk_widget().pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =========================
# SERIAL THREAD
# =========================

def serial_reader():
    global temperatura
    global arduino_prag
    global fan_state
    global rezim

    while True:

        if ser:
            try:
                line = ser.readline().decode().strip()

                if line:

                    parts = line.split(",")

                    if len(parts) == 4:

                        temperatura = float(parts[0])
                        arduino_prag = int(parts[1])
                        fan_state = int(parts[2])
                        rezim = int(parts[3])

                        # AUTO PYTHON

                        if rezim == 3:

                            if temperatura >= python_prag:
                                send_command("FAN_ON")
                            else:
                                send_command("FAN_OFF")

                        elapsed = (
                            time.time()
                            - start_time
                        )

                        x_data.append(elapsed)
                        temp_data.append(
                            temperatura
                        )

                        fan_data.append(
                            fan_state
                        )

            except:
                pass

        time.sleep(0.05)

# =========================
# GUI UPDATE
# =========================

def update_gui():

    temp_label.config(
        text=f"Temperatura: {temperatura:.1f} °C"
    )

    fan_label.config(
        text="Ventilator: ON"
        if fan_state
        else "Ventilator: OFF"
    )

    arduino_prag_label.config(
        text=f"Arduino prag: {arduino_prag} °C"
    )

    if rezim == 0:
        mode = "AUTO Arduino"

    elif rezim == 1:
        mode = "Override ON"

    elif rezim == 2:
        mode = "Override OFF"

    elif rezim == 3:
        mode = "AUTO Python"

    else:
        mode = "Unknown"

    mode_label.config(
        text=f"Rezim: {mode}"
    )

    ax.clear()

    ax.plot(
        list(x_data),
        list(temp_data),
        linewidth=2,
        label="Temperatura"
    )

    xs = list(x_data)
    fs = list(fan_data)

    if arduino_prag > 0:

        ax.axhline(
            y=arduino_prag,
            color="red",
            linestyle="--",
            linewidth=2,
            label="Arduino prag"
        )

    for i in range(len(xs) - 1):

        if fs[i] == 1:

            ax.axvspan(
                xs[i],
                xs[i + 1],
                alpha=0.2
            )

    ax.set_title(
        "Temperatura kroz vrijeme"
    )

    ax.set_xlabel(
        "Vrijeme (s)"
    )

    ax.set_ylabel(
        "Temperatura (°C)"
    )

    ax.grid(True)
    ax.legend()

    canvas.draw()

    root.after(
        1000,
        update_gui
    )

# =========================
# START
# =========================

threading.Thread(
    target=serial_reader,
    daemon=True
).start()

update_gui()

root.mainloop()
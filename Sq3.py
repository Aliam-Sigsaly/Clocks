import tkinter as tk
from tkinter import ttk
import threading
import time
import numpy as np
from collections import deque

class JammableRampCounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Jammable Ramp Counter")
        self.root.geometry("500x400")

        # Timing parameters
        self.sample_rate = 40000
        self.is_playing = False
        self.stop_counter = False
        self.counter_value = 0
        self.note_start_sample = 0
        self.current_note = 0

        # Jam parameters - with initial values
        self.note_durations = [10000, 20000]  # Two note durations
        self.note_duration_vars = [tk.IntVar(value=d) for d in self.note_durations]

        # For tracking timing accuracy
        self.sample_count = 0
        self.start_time = 0
        self.expected_samples = 0
        
        # For high-precision timing
        self.last_time = time.perf_counter()

        self.create_widgets()
        self.setup_audio_buffers()

    def setup_audio_buffers(self):
        # Buffer for smoother GUI updates
        self.normalized_buffer = deque(maxlen=100)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Play/Stop controls
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, pady=10)

        self.play_btn = ttk.Button(control_frame, text="Play", command=self.toggle_playback)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        # Jam controls for note durations
        jam_frame = ttk.LabelFrame(main_frame, text="Jam Controls", padding="5")
        jam_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        for i, var in enumerate(self.note_duration_vars):
            ttk.Label(jam_frame, text=f"Note {i+1} duration (samples):").grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            spin = ttk.Spinbox(jam_frame, from_=1000, to=100000, increment=1000,
                              textvariable=var, width=10)
            spin.grid(row=i, column=1, padx=5, pady=2)
            spin.bind('<Return>', self.update_note_durations)
            spin.bind('<FocusOut>', self.update_note_durations)

        # Counter display
        ttk.Label(main_frame, text="Counter Value:").grid(row=2, column=0, pady=5, sticky=tk.W)
        self.counter_var = tk.StringVar(value="0")
        ttk.Label(main_frame, textvariable=self.counter_var).grid(row=2, column=1, pady=5, sticky=tk.W)

        # Normalized value display
        ttk.Label(main_frame, text="Normalized Value:").grid(row=3, column=0, pady=5, sticky=tk.W)
        self.normalized_var = tk.StringVar(value="0.0000")
        ttk.Label(main_frame, textvariable=self.normalized_var).grid(row=3, column=1, pady=5, sticky=tk.W)

        # Current note info
        ttk.Label(main_frame, text="Current Note:").grid(row=4, column=0, pady=5, sticky=tk.W)
        self.note_var = tk.StringVar(value="1")
        ttk.Label(main_frame, textvariable=self.note_var).grid(row=4, column=1, pady=5, sticky=tk.W)

        # Timing diagnostics
        ttk.Label(main_frame, text="Actual Sample Rate:").grid(row=5, column=0, pady=5, sticky=tk.W)
        self.rate_var = tk.StringVar(value="0 Hz")
        ttk.Label(main_frame, textvariable=self.rate_var).grid(row=5, column=1, pady=5, sticky=tk.W)
        
        # Add expected sample rate display
        ttk.Label(main_frame, text="Expected Sample Rate:").grid(row=6, column=0, pady=5, sticky=tk.W)
        self.expected_rate_var = tk.StringVar(value=f"{self.sample_rate} Hz")
        ttk.Label(main_frame, textvariable=self.expected_rate_var).grid(row=6, column=1, pady=5, sticky=tk.W)

        # Add timing accuracy display
        ttk.Label(main_frame, text="Timing Accuracy:").grid(row=7, column=0, pady=5, sticky=tk.W)
        self.accuracy_var = tk.StringVar(value="100%")
        ttk.Label(main_frame, textvariable=self.accuracy_var).grid(row=7, column=1, pady=5, sticky=tk.W)
        
        

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def update_note_durations(self, event=None):
        # Update note durations from GUI
        for i, var in enumerate(self.note_duration_vars):
            try:
                self.note_durations[i] = max(1000, var.get())
            except tk.TclError:
                pass  # Ignore invalid values

    def toggle_playback(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        if self.is_playing:
            return

        self.is_playing = True
        self.stop_counter = False
        self.play_btn.config(text="Stop")
        self.counter_value = 0
        self.note_start_sample = 0
        self.current_note = 0
        self.sample_count = 0
        self.start_time = time.time()

        # Start counter in a separate thread
        self.counter_thread = threading.Thread(target=self.counter_loop)
        self.counter_thread.daemon = True
        self.counter_thread.start()

    def stop_playback(self):
        self.stop_counter = True
        self.is_playing = False
        self.play_btn.config(text="Play")

        # Calculate actual sample rate
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            actual_rate = self.sample_count / elapsed
            self.rate_var.set(f"{actual_rate:.0f} Hz")

    def counter_loop(self):
        sample_interval = 1.0 / self.sample_rate
        last_update_time = time.time()
        update_interval = 0.05  # Update GUI every 50ms
        next_time = time.perf_counter()
        samples_per_update = int(self.sample_rate * update_interval)

        # Pre-allocate arrays for efficiency
        counter_chunk = 0
        normalized_chunk = np.zeros(samples_per_update)

        while not self.stop_counter:
            # Process a chunk of samples for efficiency
            for i in range(samples_per_update):
                # Increment counter
                self.counter_value += 1
                self.sample_count += 1
                counter_chunk += 1

                # Check if we've reached the end of the current note
                current_note_duration = self.note_durations[self.current_note]
                elapsed_in_note = self.counter_value - self.note_start_sample

                if elapsed_in_note >= current_note_duration:
                    # Move to next note
                    self.note_start_sample = self.counter_value
                    self.current_note = (self.current_note + 1) % len(self.note_durations)
                    elapsed_in_note = 0
                    current_note_duration = self.note_durations[self.current_note]

                # Calculate normalized value
                normalized_value = elapsed_in_note / current_note_duration
                normalized_chunk[i] = normalized_value

            # Add the chunk to the buffer
            self.normalized_buffer.extend(normalized_chunk)

            # Update GUI
            current_time = time.time()
            if current_time - last_update_time >= update_interval:
                self.root.after(0, self.update_display)
                last_update_time = current_time

            # High-precision timing
            next_time += update_interval
            current_time = time.perf_counter()
            sleep_time = next_time - current_time

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # We're running behind schedule
                next_time = current_time

    def update_display(self):
        # Update all display elements
        self.counter_var.set(str(self.counter_value))

        if self.normalized_buffer:
            self.normalized_var.set(f"{self.normalized_buffer[-1]:.4f}")

        self.note_var.set(str(self.current_note + 1))

        # Update actual sample rate and timing accuracy
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            actual_rate = self.sample_count / elapsed
            self.rate_var.set(f"{actual_rate:.0f} Hz")

            # Calculate timing accuracy
            expected_samples = elapsed * self.sample_rate
            accuracy = (self.sample_count / expected_samples) * 100 if expected_samples > 0 else 0
            self.accuracy_var.set(f"{accuracy:.1f}%")

if __name__ == "__main__":
    root = tk.Tk()
    app = JammableRampCounter(root)
    root.mainloop()

import tkinter as tk
from tkinter import ttk
import threading
import time

class RampCounter:
    def __init__(self, root):
        self.root = root
        self.root.title("Ramp Counter with 40kHz Sample Rate")
        self.root.geometry("400x200")

        # Sample rate and timing variables
        self.sample_rate = 40000  # 40kHz sample rate
        self.is_playing = False
        self.counter_thread = None
        self.stop_counter = False
        self.counter_value = 0

        # Create GUI
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Play/Stop buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, pady=10)

        self.play_btn = ttk.Button(button_frame, text="Play", command=self.toggle_playback)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        # Counter display
        ttk.Label(main_frame, text="Counter Value:").grid(row=1, column=0, pady=5)
        self.counter_var = tk.StringVar(value="0")
        self.counter_spin = ttk.Spinbox(main_frame, textvariable=self.counter_var,
                                       state="readonly", width=15)
        self.counter_spin.grid(row=2, column=0, pady=5)

        # Sample rate info
        ttk.Label(main_frame, text=f"Sample Rate: {self.sample_rate} Hz").grid(row=3, column=0, pady=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def toggle_playback(self):
        """Toggle counter playback"""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """Start counter in a separate thread"""
        if self.is_playing:
            return

        self.is_playing = True
        self.stop_counter = False
        self.play_btn.config(text="Stop")

        # Start counter in a separate thread
        self.counter_thread = threading.Thread(target=self.counter_loop)
        self.counter_thread.daemon = True
        self.counter_thread.start()

    def stop_playback(self):
        """Stop counter"""
        self.stop_counter = True
        self.is_playing = False
        self.play_btn.config(text="Play")

    def counter_loop(self):
        """Counter loop running in a separate thread"""
        sample_interval = 1.0 / self.sample_rate  # Time between samples

        while not self.stop_counter:
            start_time = time.time()

            # Increment counter
            self.counter_value += 1

            # Update GUI in thread-safe way
            self.root.after(0, self.update_counter_display)

            # Calculate sleep time to maintain sample rate
            elapsed = time.time() - start_time
            sleep_time = max(0, sample_interval - elapsed)

            time.sleep(sleep_time)

    def update_counter_display(self):
        """Update the counter display (called from main thread)"""
        self.counter_var.set(str(self.counter_value))

if __name__ == "__main__":
    root = tk.Tk()
    app = RampCounter(root)
    root.mainloop()

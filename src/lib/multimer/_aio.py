import sys
import time

# --- STEP 1: Cross-Platform Environment Polyfills ---
# Detect standard Python (CPython) vs MicroPython
IS_MICROPYTHON = sys.implementation.name == "micropython"

if not IS_MICROPYTHON:
    # Polyfill MicroPython's time extensions for standard CPython
    def sleep_ms(ms):
        time.sleep(ms / 1000.0)
    
    def ticks_ms():
        return int(time.time() * 1000)
    
    def ticks_add(ticks, delta):
        return ticks + delta
    
    def ticks_diff(ticks1, ticks2):
        return ticks1 - ticks2

    # Map the unified functions to a compatible namespace
    time_sleep_ms = sleep_ms
    time_ticks_ms = ticks_ms
    time_ticks_add = ticks_add
    time_ticks_diff = ticks_diff
    
    # Standard Python uses 'threading', MicroPython uses custom '_thread'
    import threading
    def start_background_thread(target_function):
        thread = threading.Thread(target=target_function)
        thread.daemon = True # Prevents the thread from blocking script exit
        thread.start()
else:
    # Native MicroPython environment mappings
    time_sleep_ms = time.sleep_ms
    time_ticks_ms = time.ticks_ms
    time_ticks_add = time.ticks_add
    time_ticks_diff = time.ticks_diff
    
    import _thread
    def start_background_thread(target_function):
        _thread.start_new_thread(target_function, ())


# --- STEP 2: Unified Hardware/Software Timer Interface ---
try:
    from machine import Timer
    # If this succeeds (e.g., running on a microcontroller), use native hardware timers
except ImportError:
    # Drop-in Software Emulation for Linux (Both MicroPython & CPython ports)
    class Timer:
        PERIODIC = 1
        ONE_SHOT = 2

        def __init__(self, id=-1, *args, **kwargs):
            self._callback = None
            self._period = 0
            self._mode = self.PERIODIC
            self._is_running = False

        def init(self, mode=PERIODIC, period=1000, callback=None):
            """
            Initializes the software timer loop.
            :param period: Time in milliseconds
            """
            self._mode = mode
            self._period = period
            self._callback = callback
            
            if not self._is_running:
                self._is_running = True
                start_background_thread(self._run_loop)

        def deinit(self):
            """Stops the software timer execution loop."""
            self._is_running = False

        def _run_loop(self):
            # Track intervals relative to system ticks to prevent clock drift
            next_trigger = time_ticks_add(time_ticks_ms(), self._period)
            
            while self._is_running:
                # Calculate time left until the next expected execution point
                now = time_ticks_ms()
                remaining = time_ticks_diff(next_trigger, now)
                
                if remaining > 0:
                    time_sleep_ms(remaining)
                
                if not self._is_running:
                    break
                
                # Fire the event callback
                if self._callback:
                    try:
                        self._callback(self)
                    except Exception as e:
                        print(f"Error in Timer callback: {e}")
                
                if self._mode == self.ONE_SHOT:
                    self._is_running = False
                    break
                
                # Schedule the exact tick benchmark for the next cycle
                next_trigger = time_ticks_add(next_trigger, self._period)


# --- STEP 3: Cross-Platform Test Script ---
if __name__ == "__main__":
    print(f"Running on implementation: {sys.implementation.name.upper()}")
    
    counter = 0
    
    def tick_handler(t):
        global counter
        counter += 1
        print(f"[Timer Trigger] Tick #{counter} at {time.time():.2f}")
        if counter >= 5:
            print("Stopping timer execution...")
            t.deinit()

    # Instantiate the unified Timer (Hardware on ESP32/Pico, Software on Linux)
    my_timer = Timer(-1)
    my_timer.init(mode=Timer.PERIODIC, period=1000, callback=tick_handler)

    # Keep the primary thread alive while the background thread fires events
#    for _ in range(7):
#        time_sleep_ms(1000)
#    print("Main program finished.")


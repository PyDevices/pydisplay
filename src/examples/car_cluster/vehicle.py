# SPDX-License-Identifier: MIT
"""Believable vehicle state for the instrument cluster demo."""

# Target cruise speeds (mph) step by 13 per gear at full throttle (1..10).
_GEAR_MAX_MPH = (0, 13, 26, 39, 52, 65, 78, 91, 104, 117, 130)
_GEAR_MAX_RPM = (0, 6200, 6000, 5800, 5600, 5400, 5200, 5000, 4800, 4600, 4400)
_IDLE_RPM = 800
_REDLINE = 6500


def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _lerp(a, b, t):
    return a + (b - a) * t


class Vehicle:
    def __init__(self):
        self.gear = 0  # 0 = Park, 1..10
        self.throttle = 0.0
        self._throttle_target = 0.0
        self.speed_mph = 0.0
        self.rpm = 0.0
        self.fuel_frac = 0.625  # ~5/8 tank
        self.coolant_f = 210.6
        self.oil_psi = 38.0
        self.oil_temp_f = 205.0
        self.battery_v = 14.2
        self.iat_f = 95.0
        self.engine_hours = 128.4
        self.odo_miles = 48217.6
        self.speedo_mode = "digital"  # or "analog"
        self.trip_a = self._new_trip()
        self.trip_b = self._new_trip()
        self.lights = {
            "autodim": True,
            "delayed_off": True,
            "drl": True,
            "fog": False,
            "cabin": False,
            "brightness": 0.85,
            "high_beam": False,
            "turn_left": False,
            "turn_right": False,
        }
        self.tires = [
            {"name": "FL", "psi": 34.0, "temp_f": 86.0},
            {"name": "FR", "psi": 34.5, "temp_f": 87.0},
            {"name": "RL", "psi": 33.0, "temp_f": 90.0},
            {"name": "RR", "psi": 33.5, "temp_f": 89.0},
            {"name": "Spare", "psi": 40.0, "temp_f": 72.0},
        ]
        self.assist = {
            "acc": True,
            "acc_set": 65,
            "lane_keep": True,
            "blind_spot": True,
            "park_fl": 0.15,
            "park_fr": 0.18,
            "park_rl": 0.55,
            "park_rr": 0.52,
        }
        self.redline = False

    def _new_trip(self):
        return {
            "distance": 0.0,
            "time_s": 0.0,
            "fuel_used": 0.0,
            "max_speed": 0.0,
        }

    def gear_label(self):
        if self.gear <= 0:
            return "P"
        return str(int(self.gear))

    def set_gear(self, g):
        self.gear = int(_clamp(g, 0, 10))

    def set_throttle(self, t):
        self._throttle_target = _clamp(float(t), 0.0, 1.0)

    def press_digit(self, d):
        """Digit 0-9: latch gear (0→10th) and full throttle while held.

        Cruise target is gear × 13 mph (see ``_GEAR_MAX_MPH``).
        """
        d = int(d) % 10
        self.gear = 10 if d == 0 else d
        self._throttle_target = 1.0

    def release_digit(self):
        """Key up: keep gear, return toward idle throttle."""
        self._throttle_target = 0.0

    def toggle_speedo_mode(self):
        self.speedo_mode = "analog" if self.speedo_mode == "digital" else "digital"

    def reset_trip(self, which):
        if which == "a":
            self.trip_a = self._new_trip()
        elif which == "b":
            self.trip_b = self._new_trip()

    def trip_avg_speed(self, which):
        trip = self.trip_a if which == "a" else self.trip_b
        if trip["time_s"] < 1.0:
            return 0.0
        return trip["distance"] / (trip["time_s"] / 3600.0)

    def trip_mpg(self, which):
        trip = self.trip_a if which == "a" else self.trip_b
        if trip["fuel_used"] < 0.01:
            return 0.0
        return trip["distance"] / trip["fuel_used"]

    def tick(self, dt_s):
        if dt_s <= 0:
            return
        if dt_s > 0.2:
            dt_s = 0.2

        # Throttle lag
        self.throttle = _lerp(self.throttle, self._throttle_target, min(1.0, dt_s * 6.0))

        if self.gear <= 0:
            target_speed = 0.0
            target_rpm = 0.0
        else:
            g = self.gear
            thr = self.throttle
            # Idle creep when in gear with no throttle
            idle_frac = 0.08 if thr < 0.02 else 0.0
            drive = max(thr, idle_frac)
            target_speed = _GEAR_MAX_MPH[g] * drive
            target_rpm = _IDLE_RPM + (_GEAR_MAX_RPM[g] - _IDLE_RPM) * thr
            if thr < 0.02:
                target_rpm = float(_IDLE_RPM)

        # Snappy response so gear steps of 13 mph are obvious while holding a digit.
        speed_rate = 5.5 if self.gear > 0 else 4.0
        rpm_rate = 6.0
        self.speed_mph = _lerp(self.speed_mph, target_speed, min(1.0, dt_s * speed_rate))
        self.rpm = _lerp(self.rpm, target_rpm, min(1.0, dt_s * rpm_rate))
        if self.speed_mph < 0.15:
            self.speed_mph = 0.0
        if self.gear <= 0 and self.rpm < 50:
            self.rpm = 0.0

        self.redline = self.rpm >= _REDLINE

        # Coolant drifts toward ~211 under load; redline at 212 on gauge
        load = _clamp(self.throttle * 0.7 + (self.rpm / 10000.0) * 0.3, 0.0, 1.0)
        target_cool = 208.0 + load * 3.5  # ~208..211.5
        self.coolant_f = _lerp(self.coolant_f, target_cool, min(1.0, dt_s * 0.15))

        # Oil pressure tracks RPM
        if self.rpm < 100:
            target_oil = 0.0
        else:
            target_oil = 18.0 + (self.rpm / 10000.0) * 55.0
        self.oil_psi = _lerp(self.oil_psi, target_oil, min(1.0, dt_s * 2.5))

        self.oil_temp_f = _lerp(self.oil_temp_f, 190.0 + load * 30.0, min(1.0, dt_s * 0.1))
        self.iat_f = _lerp(self.iat_f, 85.0 + load * 25.0, min(1.0, dt_s * 0.08))
        self.battery_v = _lerp(self.battery_v, 13.8 + (0.6 if self.rpm > 500 else 0.0), min(1.0, dt_s))

        # Fuel burn ~0.00002 tank/s at cruise
        burn = (0.000005 + self.throttle * 0.00004 + self.speed_mph * 0.00000015) * dt_s
        self.fuel_frac = _clamp(self.fuel_frac - burn, 0.0, 1.0)

        dist = self.speed_mph * (dt_s / 3600.0)
        self.odo_miles += dist
        if self.rpm > 100:
            self.engine_hours += dt_s / 3600.0

        for trip in (self.trip_a, self.trip_b):
            if self.speed_mph > 0.5:
                trip["distance"] += dist
                trip["time_s"] += dt_s
                trip["fuel_used"] += burn * 12.0  # crude gallons from tank frac
                if self.speed_mph > trip["max_speed"]:
                    trip["max_speed"] = self.speed_mph

        # Tire heat with speed
        for tire in self.tires:
            if tire["name"] == "Spare":
                continue
            target_t = 75.0 + self.speed_mph * 0.25
            tire["temp_f"] = _lerp(tire["temp_f"], target_t, min(1.0, dt_s * 0.05))

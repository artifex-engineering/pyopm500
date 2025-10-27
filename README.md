# pyopm500
[![License](https://img.shields.io/github/license/artifex-engineering/pyopm500)](https://github.com/artifex-engineering/pyopm500/blob/main/LICENSE)
![PyPI - Status](https://img.shields.io/pypi/status/pyopm500)
![PyPI - Version](https://img.shields.io/pypi/v/pyopm500)

**Python library for the Artifex Engineering OPM500**


## Installation
Install via pip:
```bash
pip install pyopm500
```

Install manually:
```bash
git clone https://github.com/artifex-engineering/pyopm500.git
cd pyopm500
pip install .
```

## Usage
```python
from pyopm500 import OPM500, GAIN, UNITS, BANDWITH

# List all available devices
devices = OPM500.find_devices() # Get all available devices
print("Available Devices: {}\n\n".format(", ".join(devices) if len(devices) > 0 else "None"))

# Create OPM500 instance
opm = OPM500()

# Connect to first OPM500 device in list
opm.connect(devices[0])

opm.opm_set_polarity(False) # Set polarity to not inverted

opm.opm_set_auto_zero() # Set initial auto zero

# Or set initial auto zero reset
opm.opm_set_auto_zero_reset()


opm.opm_set_bandwith(BANDWITH.KHZ_10) # Set bandwith to 100 kHz

# Set wavelength
opm.opm_set_wavelength(660)

# Set gain
opm.opm_set_gain(GAIN.X1)

# Set unit to use in measurements
opm.set_unit(UNITS.MICROAMPERE)

# Print single measurement
print(format(opm.opm_get_measurement(), '.8f'))

opm.disconnect()
```

## Query current states and device informations
```python
print("Firmware version: {}".format(opm.opm_firmware_version))
print("Serial number: {}".format(opm.opm_serial_number))
print("Date of manufacturing: {}".format(opm.opm_date_of_manufacturing))

print("Detector min wavelength: {}".format(opm.opm_detector_min_wavelength))
print("Detector max wavelength: {}".format(opm.opm_detector_max_wavelength))

print("Device info:\n{}\n\n".format(opm.opm_get_info()))

print("Current bandwith: {}".format(opm.opm_get_bandwith()))
print("Current wavelength: {}".format(opm.opm_get_wavelength()))
print("Current gain: {}".format(opm.opm_get_gain()))
print("Current Unit: {}".format(opm.unit))
print("Current filter factor: {}\n\n".format(opm.filter))
```

## nW/cm², µW/cm², mW/cm², W/cm²
```python
opm.set_unit(UNITS.MICROWATTS_PER_SQUARE_CENTIMETER) # Set unit to use in measurements

opm.aperture_in_mm = 7.0 # Set aperture in mm
print("Current Aperture in mm: {}".format(opm.aperture_in_mm)) # Print aperture in mm

measurement_value = opm.opm_get_measurement() # Get measurement value in specified unit
print("Measurement Value: {}{}".format(measurement_value[0], measurement_value[1])) # measurement value in specified unit
```

## Available Units
- **Nanoampere (nA)**: UNITS.NANOAMPERE
- **Microampere (µA)**: UNITS.MICROAMPERE
- **Milliampere (mA)**: UNITS.MILLIAMPERE
- **Ampere (A)**: UNITS.AMPERE
- **Nanowatts (nW)**: UNITS.NANOWATTS
- **Microwatts (µW)**: UNITS.MICROWATTS
- **Milliwatts (mW)**: UNITS.MILLIWATTS
- **Watts (W)**: UNITS.WATTS
- **Nanowatts per square centimeter (nW/cm²)**: UNITS.NANOWATTS_PER_SQUARE_CENTIMETER
- **Microwatts per square centimeter (µW/cm²)**: UNITS.MICROWATTS_PER_SQUARE_CENTIMETER
- **Milliwatts per square centimeter (mW/cm²)**: UNITS.MILLIWATTS_PER_SQUARE_CENTIMETER
- **Watts per square centimeter (W/cm²)**: UNITS.WATTS_PER_SQUARE_CENTIMETER
- **Decibel-milliwatts (dBm)**: UNITS.DECIBEL_MILLIWATTS

## Gain levels:
- **x1**: GAIN.X1
- **x10**: GAIN.X10
- **x100**: GAIN.X100
- **x1000**: GAIN.X1000
- **x10000**: GAIN.X10000
- **x100000**: GAIN.X100000
- **Auto**: GAIN.AUTO

## Bandwiths
- **10 kHz**: BANDWITH.KHZ_10
- **1 kHz**: BANDWITH.KHZ_1
- **100 Hz**: BANDWITH.HZ_100
- **10 Hz**: BANDWITH.HZ_10
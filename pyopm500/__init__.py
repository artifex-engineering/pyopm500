# MIT License
#
# Copyright (c) 2025 Artifex Engineering GmbH & Co KG.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import re
import sys
import math
import ftd2xx
from enum import Enum
from time import sleep


class BANDWITH(Enum):
    KHZ_10 = "10 kHz"
    KHZ_1 = "1 kHz"
    HZ_100 = "100 Hz"
    HZ_10 = "10 Hz"

class INITIAL_AUTO_ZERO(Enum):
    NONE = "None"
    AUTO_ZERO = "Auto zero"
    AUTO_ZERO_RESET = "Auto zero reset"

class GAIN(Enum):
    X1 = "x1"
    X10 = "x10"
    X100 = "x100"
    X1000 = "x1000"
    X10000 = "x10000"
    X100000 = "x1000000"
    AUTO = "auto-gain"

class UNITS(Enum):
    NANOAMPERE = "nA"
    MICROAMPERE = "µA"
    MILLIAMPERE = "mA"
    AMPERE = "A"
    NANOWATTS = "nW"
    MICROWATTS = "µw"
    MILLIWATTS = "mW"
    WATTS = "W"
    NANOWATTS_PER_SQUARE_CENTIMETER = "nW/cm²"
    MICROWATTS_PER_SQUARE_CENTIMETER = "µW/cm²"
    MILLIWATTS_PER_SQUARE_CENTIMETER = "mW/cm²"
    WATTS_PER_SQUARE_CENTIMETER = "W/cm²"
    DECIBEL_MILLIWATTS = "dBm"

class OPM500():
    def __init__(self) -> None :
        """
        Initializes the OPM500 class.
        """
        self._unit: str = UNITS.MICROAMPERE.value

        self._port: str = ""
        self._device = None

        self._bandwith_steps: dict = {
            "10 kHz": "B1",
            "1 kHz": "B2",
            "100 Hz": "B3",
            "10 Hz": "B4"
        }

        self._gain_steps: dict = {
            "x1": "V1",
            "x10": "V2",
            "x100": "V3",
            "x1000": "V4",
            "x10000": "V5",
            "x100000": "V6",
            "auto-gain": "auto-gain"
        }

        self._units: dict = {
            "nA": "Nanoampere (nA)",
            "µA": "Microampere (µA)",
            "mA": "Milliampere (mA)",
            "A": "Ampere (A)",
            "nW": "Nanowatts (nW)",
            "µW": "Microwatts (µW)",
            "mW": "Milliwatts (mW)",
            "W": "Watts (W)",
            "nW/cm²": "Nanowatts per square centimeter (nW/cm²)",
            "µW/cm²": "Microwatts per square centimeter (µW/cm²)",
            "mW/cm²": "Milliwatts per square centimeter (mW/cm²)",
            "W/cm²": "Watts per square centimeter (W/cm²)",
            "dBm": "Decibel-milliwatts (dBm)"
        }
        self._sensitivity: float = 1.0
        self._wavelength: int = 660
        self._initial_auto_zero: str = INITIAL_AUTO_ZERO.NONE.value
        self._invert_input_polarity: bool = False
        self._bandwith: str = BANDWITH.KHZ_10.value
        self._autogain_gain: int = None
        self._gain: str = GAIN.X1.value
        self._max_gain: int = len(self._gain_steps) - 1
        self._filter: float = 1.0
        self._aperture: float = 7.0

        self._opm_comm_max_retries: int = 800

        self._opm_fw: str = None
        self._opm_serial: str = None
        self._opm_date_of_manufacturing: str = None

        self._opm_detector_min_wavelength: int = None
        self._opm_detector_max_wavelength: int = None
    
    @property
    def unit(self) -> str:
        return self._units[self._unit]
    
    @property
    def filter(self) -> float:
        return self._filter
    
    @filter.setter
    def filter(self, value: float) -> None:
        self._filter = float(value)
    
    @property
    def aperture_in_mm(self) -> float:
        return self._aperture
    
    @aperture_in_mm.setter
    def aperture_in_mm(self, value: float) -> float:
        self._aperture = float(value)
    
    @property
    def initial_auto_zero(self) -> str:
        return self._initial_auto_zero
    
    @property
    def invert_input_polarity(self) -> str:
        return self._invert_input_polarity

    @property
    def opm_firmware_version(self) -> str:
        return self._opm_fw
    
    @property
    def opm_serial_number(self) -> str:
        return self._opm_serial
    
    @property
    def opm_date_of_manufacturing(self) -> str:
        return self._opm_date_of_manufacturing
    
    @property
    def opm_detector_min_wavelength(self) -> int:
        return self._opm_detector_min_wavelength
    
    @property
    def opm_detector_max_wavelength(self) -> int:
        return self._opm_detector_max_wavelength
    
    @staticmethod
    def find_devices() -> list[str]:
        """
        Return list of found devices

        :result:
            found_devices(list[str]): list of found OPM500 devices
        """
        devices_found = []

        if sys.platform != "win32":
            ftd2xx.setVIDPID(0x0403, 0x9a68) # for linux and macOS

        numDevs = ftd2xx.createDeviceInfoList()

        for i in range(0, numDevs):
            dev = ftd2xx.getDeviceInfoDetail(i)
            if "OPM500" in dev["description"].decode(errors="ignore"):
                devices_found.append("{} - {}".format(dev["description"].decode(errors="ignore"), dev["serial"].decode(errors="ignore")))

        return devices_found
    
    def connect(self, device: str) -> None:
        """
        Connects to OPM500 and initializes it

        :param:
            device(str): Device string in the format "OPM500 - serial_number" E.g. "OPM500 - 12345"
        
        :return:
            result(bool): Returns whether the device was successfully connected and initialized.
        """

        if self._device != None:
            return False

        if device == "":
            raise Exception("No port selected.")
        self._port = device.split("- ")[1]

        # Open device
        try:
            self._device = ftd2xx.openEx(self._port.encode())
            self._device.setBaudRate(115200)
            self._device.setDataCharacteristics(8, 0, 0) # 8 data bits, 1 stop bit, no parity
            self._device.setFlowControl(0, 0, 0) # no flow control
            self._device.setTimeouts(1000, 0)
            self._device.setChars(126, 1, 0, 0)
            self._device.resetDevice()
            self._device.purge()
        except ftd2xx.DeviceError:
            raise Exception("Cannot open Device with serial number {}.".format(self._port))
        
        self._opm_send("$U")
        if self._opm_recv() != "U OK":
            self.disconnect()
            return False

        if not self._initialize():
            self.disconnect()
            return False
        return True
    
    def _opm_send(self, msg: str):
        if self._device is None:
            raise Exception("Send error: port not open.")
        self._device.purge()
        self._device.write(msg.encode())
    
    def _opm_recv(self) -> str:
        if self._device is None:
            raise Exception("recive error: port not open.")
        msg = b""
        i = 0
        while i < self._opm_comm_max_retries:
            if self._device.getQueueStatus() > 0: # check if bytes in buffer
                msg = self._device.read(self._device.getQueueStatus()) # read entire buffer
                while not msg.endswith(b'\r'): # append buffer until '\r' is found
                    msg = msg + self._device.read(self._device.getQueueStatus())

                return msg.decode(errors="ignore").replace("\r", '').strip()
            sleep(0.01)
            i += 1
        raise TimeoutError("No Valid Data received.")

    def _initialize(self) -> bool:
        info = self.opm_get_info()

        if re.sub(r"^(opm500)(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE) != "OPM500":
            return False

        regex_fw = re.sub(r"^opm500.*fw.*?([0-9]*\.[0-9]*)(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)
        regex_serial = re.sub(r"(?:\n|.*$)*serial:.*?([0-9]+)(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)
        regex_date_of_manufacturing = re.sub(r"(?:\n|.*$)*date of manufacturing:.*?([0-9]{1,2}/[0-9]{2,4})(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)

        regex_detector_min_wavelength = re.sub(r"(?:\n|.*$)*detector:.*?([0-9]+)nm(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)
        regex_detector_max_wavelength = re.sub(r"(?:\n|.*$)*detector:.*?(?:[0-9]+)nm.*?([0-9]+)nm(?:\n|.*$)*", "\\1", info, count=0, flags=re.MULTILINE | re.IGNORECASE)

        self._opm_fw = regex_fw if regex_fw != info else "" # get OPM500 Firmware version

        self._opm_serial = regex_serial if regex_serial != info else "" # get OPM500 serial number
        self._opm_date_of_manufacturing = regex_date_of_manufacturing if regex_date_of_manufacturing != info else "" # get OPM500 date of Manufacturing

        self._opm_detector_min_wavelength = int(regex_detector_min_wavelength) if regex_detector_min_wavelength != info else -1 # get detector min wavelength
        self._opm_detector_max_wavelength = int(regex_detector_max_wavelength) if regex_detector_max_wavelength != info else -1 # get detector max wavelength

        if not self.opm_set_auto_zero_reset():
            self.disconnect()
            return False
    
        # set default values
        if not self.opm_set_wavelength(self._wavelength):
            return False
        
        if not self.opm_set_gain(self._gain):
            return False

        return True

    def opm_get_info(self) -> str:
        """
        Returns the device info as a printable string.

        :return:
            info(str): Printable device info
        """
        self._opm_send("$I")
        return self._opm_recv()
    
    def set_unit(self, unit: UNITS) -> bool:
        """
        Sets the specified unit as the unit used for measurements.

        :param:
            unit(UNITS): Unit to use for measurements
        
        :return:
            result(bool): Returns whether the unit was set successfully
        """
        if unit not in UNITS:
            return False
        self._unit = unit.value
        return True
    
    def opm_is_polarity_inverted(self) -> bool | None:
        """
        Returns whether the polarity is inverted or not.

        :return:
            is_polarity_inverted(bool): True if the polarity is inverted
        """
        self._opm_send("$F")
        received = self._opm_recv()

        if received == "F0":
            self._invert_input_polarity = False
            return False
        elif received == "F1":
            self._invert_input_polarity = True
            return True
        else:
            return None
    
    def opm_set_polarity(self, invert_polarity: bool) -> bool:
        """
        Sets whether the polarity should be inverted or not.

        :param:
            invert_polarity(bool): Whether the polarity should be inverted or not
        
        :return:
            result(bool): Returns whether the polarity was set successfully
        """
        invert_polarity = bool(invert_polarity)

        polarity_command = "N" if invert_polarity == False else "C"
        
        self._opm_send("${}".format(polarity_command))

        recv = self._opm_recv()
        if recv == "{} OK".format(polarity_command):
            self._invert_input_polarity = invert_polarity
            return True
        return False

    def opm_get_wavelength(self) -> int:
        """
        Return the current wavelength:

        :return:
            wavelength(int): Current wavelength
        """
        return self._wavelength

    def opm_set_wavelength(self, wavelength: int) -> bool:
        """
        Sets the specified wavelength.

        :param:
            wavelength(int): Wavelength

        :return:
            result(bool): Returns whether the wavelength was set successfully
        """
        if wavelength not in range(self._opm_detector_min_wavelength, self._opm_detector_max_wavelength + 1):
            return False
        
        tmp_wavelength = wavelength
        wavelength = str(wavelength).zfill(4) # convert to string append 0 at beginning of wavelength if wavelength is not 4 bytes long

        self._opm_send("L")
        for i in wavelength:
            self._opm_send(i)
        recv = self._opm_recv()

        if recv.count("KF:") > 0:
            self._wavelength = tmp_wavelength
            self._sensitivity = float(recv.replace("KF:", '').replace(',', '.').strip()) # retrieve correction factor from OPM500
            return True
        return False
    
    def opm_get_bandwith(self) -> str | None:
        """
        Returns the current bandwith.

        :return:
            bandwith(str): Current bandwith in format: 10 kHz, 1 kHz, ...
        """
        self._opm_send("B?")
        received = self._opm_recv()

        if received in self._bandwith_steps.values():
            self._bandwith = dict(zip(self._bandwith_steps.values(), self._bandwith_steps.keys()))[received]
            return self._bandwith
        return None
    
    def opm_set_bandwith(self, bandwith: str | BANDWITH) -> bool:
        """
        Sets the specified bandwith.

        :param:
            bandwith(str | BANDWITH): Gain to set
        
        :return:
            result(bool): Returns whether the bandwith was set successfully
        """
        if type(bandwith) == BANDWITH:
            bandwith = str(bandwith.value)

        if bandwith not in self._bandwith_steps.keys():
            raise Exception("Invalid bandwith. choose one from the pre-defined bandwiths.")
        
        self._opm_send(self._bandwith_steps[bandwith])
        recv = self._opm_recv()
        if recv == "{} OK".format(self._bandwith_steps[bandwith]):
            self._bandwith = bandwith
            return True
        return False

    def opm_get_gain(self) -> str | None:
        """
        Returns the current gain.

        :return:
            gain(str): Current gain in format: x1, x10, ...
        """
        self._opm_send("V?")
        received = self._opm_recv()
        
        gain = received.splitlines()
        if gain[0] == "V? OK" and gain[1] in self._gain_steps.values():
            if self._gain != "auto-gain":
                self._gain = dict(zip(self._gain_steps.values(), self._gain_steps.keys()))[gain[1]]
            self._autogain_gain = int(self._gain_steps[dict(zip(self._gain_steps.values(), self._gain_steps.keys()))[gain[1]]][1:])
            return dict(zip(self._gain_steps.values(), self._gain_steps.keys()))[gain[1]]
        return None
    
    def opm_set_gain(self, gain: str | GAIN) -> bool:
        """
        Sets the specified gain.

        :param:
            gain(str | GAIN): Gain to set
        
        :return:
            result(bool): Returns whether the gain was set successfully
        """
        if type(gain) == GAIN:
            gain = str(gain.value)

        if gain not in self._gain_steps.keys():
            raise Exception("Invalid gain. choose one from the pre-defined gains.")

        if gain == "auto-gain":
            self._gain = gain
            return True
        
        self._opm_send(self._gain_steps[gain])
        recv = self._opm_recv()
        if recv == "{} OK".format(self._gain_steps[gain]):
            if self._gain != "auto-gain":
                self._gain = gain
            self._autogain_gain = int(self._gain_steps[gain][1:])
            return True
        return False

    def opm_set_auto_zero(self) -> bool:
        self._opm_send("$A")
        
        recv = self._opm_recv()
        if recv.count("Gain: ") > 0:
            self._initial_auto_zero = INITIAL_AUTO_ZERO.AUTO_ZERO.value
            self._max_gain = int(recv[-1])
            sleep(0.2)
            return True
        elif recv.count("A OK") > 0:
            self._initial_auto_zero = INITIAL_AUTO_ZERO.AUTO_ZERO.value
            self._max_gain = len(self._gain_steps) - 1
            sleep(0.5)
            return True
        return False
    
    def opm_set_auto_zero_reset(self) -> bool:
        self._opm_send("$R")

        recv = self._opm_recv()
        if recv == "R OK":
            self._initial_auto_zero = INITIAL_AUTO_ZERO.AUTO_ZERO.value
            self._max_gain = len(self._gain_steps) - 1
            sleep(0.05)
            return True
        return False

    def _opm_autogain(self, tmp_amplitude: str, recursion: int = 0, last_operation: int = 0) -> str:
        """
        This function automatically adjusts the gain by checking whether the
        measured value is too high or too low and then setting a new gain until
        the measured value is within a valid range.
        """
        if recursion >= len(self._gain_steps):
            return tmp_amplitude
        
        if self._autogain_gain is None:
            self.opm_get_gain() # get gain as int if not already set

        amplitude = float(tmp_amplitude[:-2].replace(",", "."))

        level = 0.0

        # To calculate if the gain needs to be moved up or down:
        # The maximum output value in percent of each gain level is represented by the numbers (122.85, 12.285, ...)
        #
        # 1. Convert the measure amplitude into percent:
        #    if gain 1: amplitude / 122.85
        #    if gain 2: amplitude / 12.285
        #    if gain 3: amplitude / 1.2285
        #    if gain 4: amplitude / 122.85
        #    if gain 5: amplitude / 12.285
        #    if gain 6: amplitude / 1.2285
        # 2. If the value in percent is above 90 and the set gain level is greater than 1, set the new gain to gain - 1.
        #    If the value in percent is below 8 and the set gain level is lower than 5, set new gain to gain + 1

        if self._autogain_gain == 1:
            level = amplitude / 122.85
        elif self._autogain_gain == 2:
            level = amplitude / 12.285
        elif self._autogain_gain == 3:
            level = amplitude / 1.2285
        elif self._autogain_gain == 4:
            level = amplitude / 122.85 # This is not a typo
        elif self._autogain_gain == 5:
            level = amplitude / 12.285 # This is not a typo
        elif self._autogain_gain == 6:
            level = amplitude / 1.2285 # This is not a typo

        if level > 90.0 and self._autogain_gain > 1:
            self._autogain_gain -= 1
            self.opm_set_gain(dict(zip(self._gain_steps.values(), self._gain_steps.keys()))["V{}".format(self._autogain_gain)]) # set new gain
            return self._opm_autogain(self.opm_get_single_raw_measure(), recursion + 1, 1) # return new measurement or re-adjust gain
        elif level < 8.0 and self._autogain_gain < self._max_gain:
            if last_operation == 1: # prevent jumping between to gain leves
                recursion = len(self._gain_steps)
            self._autogain_gain += 1
            self.opm_set_gain(dict(zip(self._gain_steps.values(), self._gain_steps.keys()))["V{}".format(self._autogain_gain)]) # set new gain
            return self._opm_autogain(self.opm_get_single_raw_measure(), recursion + 1, 2) # return new measurement or re-adjust gain
        else:
            return tmp_amplitude

    def opm_get_single_raw_measure(self) -> str:
        """
        Returns a single raw measurement result in the format: I1,0nA or I1,0uA

        :return:
            measurement(str): Raw measurement value in the format: I1,0nA or I1,0uA
        """
        self._opm_send("$E")
        return self._opm_recv()[1:].strip() # remove 'I' prefix from response

    def opm_get_measurement(self) -> list[float, str]:
        """
        This function returns a single measurement value in the selected unit..

        :return:
            list[value(float): Measured value, unit(str): Selected unit]
        """
        amplitude = self.opm_get_single_raw_measure()
        if self._gain == "auto-gain": # adjust gain if auto-gain is chosen
            amplitude = self._opm_autogain(amplitude)
        unit = amplitude[amplitude.find("A")-1:] # get unit from last two bytes of the response

        amplitude = amplitude[:-2].replace(",", ".")
        amplitude = float(amplitude)

        if unit == "uA":
            amplitude *= 1000 # convert µA to nA

        sensitivity = 1.0
        if self._unit not in ["nA", "µA", "mA", "A"]:
            sensitivity = self._sensitivity
        
        amplitude = amplitude / (sensitivity * self._filter)
        
        if self._unit.startswith("n"):
            amplitude = round(amplitude, 3)
        elif self._unit.startswith("µ"):
            amplitude /= 1000 # nano to micro
            amplitude = round(amplitude, 6)
        elif self._unit.startswith("m"):
            amplitude /= 1000000 # nano to milli
            amplitude = round(amplitude, 9)
        elif self._unit == "dBm":
            amplitude = 10 * math.log10(amplitude / 1000000)
            amplitude = round(amplitude, 5)
        else:
            amplitude /= 1000000000 # for A and W
            amplitude = round(amplitude, 12)
            
        if self._unit in ["nW/cm²", "µW/cm²", "mW/cm²", "W/cm²"]:
            amplitude = amplitude / (((self._aperture**2) / 400) * math.pi)

        return [amplitude, self._unit]
    
    def disconnect(self) -> None:
        """
        Disconnects the connected device.
        """
        if self._device is not None:
            self._device.close()
            self._device = None
        self.__init__()

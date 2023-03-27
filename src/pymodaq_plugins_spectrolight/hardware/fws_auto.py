# -*- coding: utf-8 -*-
"""
Created the 30/01/2023

@author: Sebastien Weber

Wrapper around the dll library: FWS Auto DLL
From documentation:
https://www.spectrolightinc.com/board/detail/1/?board_id=140

"""

import os
import sys
from pathlib import Path
from typing import List, Union, Tuple
from time import sleep, perf_counter
import clr
from System import String, Double

from pymodaq_plugins_spectrolight import set_logger, get_module_name

from pymodaq.daq_utils import daq_utils as dutils
from pymodaq.daq_utils.messenger import messagebox


logger = set_logger(get_module_name(__file__))


if dutils.is_64bits():
    path_dll = str(Path(r'C:\SLI'))
else:
    messagebox(severity='critical', title='FWS-Auto Dll', text='The dll is only available for 64bits systems')

sys.path.append(path_dll)
polydll = clr.AddReference('PolyDLL')

from ISM_Device import ClassPoly  # ISM_Device is the assembly name within PolyDll, found this using dotPeek
# application over the dll. ClasPoly is the .net object to use for communication and described in the documentation


class PolyError(Exception):
    pass


class FWSAuto:
    def __init__(self):
        self._net_wrapper = ClassPoly()
        self._cw: float = 532.
        self._fwhm: int = 5
        self._calib_path: str = None

        self._timeout = 10  # s
        self._start_time = 0.

    def connect(self, calibration_path: Union[str, Path]) -> str:
        self._calib_path = str(calibration_path)
        ret = self._net_wrapper.PolyConnect(String(str(calibration_path)))
        return self._net_wrapper.GetStringMsg(ret)

    def disconnect(self) -> str:
        ret = self._net_wrapper.Disconnect()
        return self._net_wrapper.GetStringMsg(ret)

    def get_device_status(self) -> str:
        ret = self._net_wrapper.GetDeviceStatus()
        return self._net_wrapper.GetStringMsg(ret)

    def is_device_ready(self) -> bool:
        ret = self._net_wrapper.GetDeviceStatus()
        return ret == 6

    def is_device_enabled(self) -> bool:
        ret = self._net_wrapper.GetDeviceEnabled()
        return bool(ret)

    def get_com_port(self) -> str:
        ret = self._net_wrapper.GetComPortNumber()
        return str(ret)

    def get_device_info(self) -> Tuple[str]:
        ret, model, serial, range = self._net_wrapper.GetInforData(String(''), String(''), String(''))
        if ret != 0:
            raise PolyError(self._net_wrapper.GetStringMsg(ret))
        return model, serial, range

    def _wait_device_ready(self):
        self._start_time = perf_counter()
        while not self.is_device_ready():
            sleep(0.5)
            if perf_counter() - self._start_time > self._timeout:
                logger.info('Timeout from the FWSPoly')
                break

    @property
    def cw_fwhm(self) -> Tuple[float]:
        """Get/Set the wavelength and the full width at half maximum in nm.
        cw_fwhm is set as a Tuple of floats with the central wavelength and the full width at half maximum in nm"""
        ret, sw, cw, lw, fwhm = self._net_wrapper.GetCurrentWavelength('', '', '', '')
        if ret != 0:
            raise PolyError(self._net_wrapper.GetStringMsg(ret))
        if ',' in cw:
            cw = cw.replace(',', '.')
            fwhm = fwhm.replace(',', '.')
        self._cw, self._fwhm = float(cw), float(fwhm)
        return self._cw, self._fwhm

    @cw_fwhm.setter
    def cw_fwhm(self, cw_fwhm: Tuple[float]):
        ret = self._net_wrapper.SetWavelength(cw_fwhm[0], cw_fwhm[1])
        if ret == 0:
            self._cw, self._fwhm = cw_fwhm[0], cw_fwhm[1]
        else:
            raise IOError(f'SetWavelength: {self._net_wrapper.GetStringMsg(ret)}')

    def set_cw_fwhm_from_internal(self):
        self.cw_fwhm = self._cw, self._fwhm

    @property
    def cw(self) -> float:
        self._cw, self._fwhm = self.cw_fwhm
        return self._cw

    @cw.setter
    def cw(self, cw: float):
        self.cw_fwhm = (cw, self._fwhm)

    @property
    def fwhm(self) -> float:
        self._cw, self._fwhm = self.cw_fwhm
        return self._fwhm

    @fwhm.setter
    def fwhm(self, fwhm: float):
        self.cw_fwhm = (self._cw, fwhm)

    def no_filtering(self) -> str:
        ret = self._net_wrapper.GoBlankPosition()
        return self._net_wrapper.GetStringMsg(ret)

    def reset(self) -> str:
        ret = self._net_wrapper.DeviceReset()
        return self._net_wrapper.GetStringMsg(ret)


if __name__ == '__main__':
    fws = FWSAuto()
    msg = fws.connect(r'C:\SLI\20220818_FAPVIS00222.ism')
    print(msg)
    try:
        print(f'COM: {fws.get_com_port()}')
        print(f'Infos: {fws.get_device_info()}')

        msg = fws.get_device_status()
        print(msg)

        fws.cw_fwhm = (530, 5)
        msg = fws.get_device_status()
        print(msg)
        print(f'Center wl, FWHM: {fws.cw_fwhm}')

        fws.cw = 550
        msg = fws.get_device_status()
        print(msg)
        print(f'Center wl: {fws.cw}')

        fws.fwhm = 7
        msg = fws.get_device_status()
        print(msg)
        print(f'FWHM: {fws.fwhm}')

    except PolyError as pe:
        print(str(pe))
    finally:
        fws.disconnect()

    
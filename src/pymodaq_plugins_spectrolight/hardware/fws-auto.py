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
from time import sleep
import clr
from System import String

from pymodaq.daq_utils import daq_utils as utils
from pymodaq.daq_utils.messenger import messagebox
from pymodaq.daq_utils.enums import BaseEnum

logger = utils.set_logger(utils.get_module_name(__file__))


if utils.is_64bits():
    path_dll = str(Path(r'C:\FWSPoly'))
else:
    messagebox(severity='critical', title='FWS-Auto Dll', text='The dll is only available for 64bits systems')

sys.path.append(path_dll)
polydll = clr.AddReference('PolyDLL')

from ISM_Device import ClassPoly  # ISM_Device is the assembly name within PolyDll, found this using dotPeek
# application over the dll. ClasPoly is the .net object to use for communication and described in the documentation


class PolyMsgEnum(BaseEnum):
    MSG_NO_ERROR = 0
    MSG_DEVICE_SEARCHING = 1
    MSG_CONNECTION_OK = 2
    MSG_SET_WAVE_OK = 3
    MSG_DEVICE_INIT = 4
    MSG_DEVICE_BUSY = 5
    MSG_DEVICE_READY = 6
    MSG_DEVICE_CLOSE_PORT = 10
    ERR_DEVICE_NOT_FOUND = -1
    ERR_DEVICE_FILE_NOT_FOUND = -2
    ERR_DEVICE_FILE_ERROR = -3
    ERR_DEVICE_NOT_READY = -4
    ERR_DEVICE = -5
    ERR_DEVICE_ERROR_MODEL_NO = -6
    ERR_DEVICE_ERROR_SERIAL_NO = -7
    ERR_DEVICE_ERROR_WAVE_RANGE = -8
    ERR_DEVICE_NOTCONNECTED = -9
    ERR_COMM_CONN_ERROR = -11
    ERR_COMM_CONN_LOST = -12
    ERR_COMM_TIMEOUT = -13
    ERR_COMM_ERROR = -14
    ERR_NOT_FOUND_WAVE = -21
    ERR_SET_WAVE_ERROR = -22


MSG_CLEAR = dict(
    MSG_NO_ERROR='The command has been executed properly.',
    MSG_DEVICE_SEARCHING='Searching for device.',
    MSG_CONNECTION_OK='Device is connected.',
    MSG_SET_WAVE_OK='Successfully changed CWL and FWHM.',
    MSG_DEVICE_INIT='Device is initializing.',
    MSG_DEVICE_BUSY='Device is busy.',
    MSG_DEVICE_READY='Device is ready.',
    MSG_DEVICE_CLOSE_PORT='Device is not ready.',
    ERR_DEVICE_NOT_FOUND='Device not found.',
    ERR_DEVICE_FILE_NOT_FOUND='Calibration file not found.',
    ERR_DEVICE_FILE_ERROR='Calibration file error.',
    ERR_DEVICE_NOT_READY='Device is busy.',
    ERR_DEVICE='Communication error.',
    ERR_DEVICE_ERROR_MODEL_NO='Calibration file and model number doesn’t match.',
    ERR_DEVICE_ERROR_SERIAL_NO='Calibration file and serial number doesn’t match.',
    ERR_DEVICE_ERROR_WAVE_RANGE='Calibration file and wavelength range doesn’t match.',
    ERR_DEVICE_NOTCONNECTED='Device is not connected.',
    ERR_COMM_CONN_ERROR='Communication error.',
    ERR_COMM_CONN_LOST='Device disconnected.',
    ERR_COMM_TIMEOUT='Communication timeout.',
    ERR_COMM_ERROR='Communication command internal error.',
    ERR_NOT_FOUND_WAVE='Wavelength out of range.',
    ERR_SET_WAVE_ERROR='Returning of error for GetCurrentWavelength due to absence of Set wavelength'
                       'because of SetWavelength command error',
)

class PolyMsg:
    def __init__(self, code: int):
        self.code = code
        self.message: str = get_message_from_code(code)


def check_error_messages():
    for key in MSG_CLEAR:
        assert key in PolyMsgEnum.names()


def get_message_from_code(code: int):
    return MSG_CLEAR[PolyMsgEnum(code).name]


class PolyError(Exception):
    pass


check_error_messages()  #make sure there is a corresponding enum name for each message in clear


class FWSAuto:
    def __init__(self):
        self._net_wrapper = ClassPoly()

    def connect(self, calibration_path: Union[str, Path]) -> PolyMsg:
        ret = self._net_wrapper.PolyConnect(String(str(calibration_path)))
        return PolyMsg(ret)

    def disconnect(self) -> PolyMsg:
        ret = self._net_wrapper.Disconnect()
        return PolyMsg(ret)

    def get_device_status(self) -> PolyMsg:
        ret = self._net_wrapper.GetDeviceStatus()
        return PolyMsg(ret)

    def is_device_enabled(self) -> bool:
        ret = self._net_wrapper.GetDeviceEnabled()
        return bool(ret)

    def get_com_port(self) -> str:
        ret = self._net_wrapper.GetComPortNumber()
        return str(ret)

    def get_device_info(self) -> Tuple[str]:
        ret, model, serial, range = self._net_wrapper.GetInforData(String(''), String(''), String(''))
        if ret != 0:
            raise PolyError(get_message_from_code(ret))
        return model, serial, range

    @property
    def wavelength(self) -> Tuple[float]:
        ret, sw, cw, lw, fwhm = self._net_wrapper.GetCurrentWavelength(String(''), String(''), String(''), String(''))
        if ret != 0:
            raise PolyError(get_message_from_code(ret))
        return float(cw), float(fwhm)

    @wavelength.setter
    def wavelength(self, cw_fwhm: Tuple[float]):
        cw = String(str(cw_fwhm[0]))
        fwhm = String(str(cw_fwhm[1]))
        ret = self._net_wrapper.SetWavelength(cw, fwhm)

    def no_filtering(self) -> PolyMsg:
        ret = self._net_wrapper.GoBlankPosition()
        return PolyMsg(ret)

    def reset(self) -> PolyMsg:
        ret = self._net_wrapper.DeviceReset()
        return PolyMsg(ret)


if __name__ == '__main__':
    fws = FWSAuto()
    msg = fws.connect(r'C:\FWSPoly\20220818_FAPVIS00222.ism')
    if not (msg.code == 0 and fws.is_device_enabled()):
        print(msg.message)
    else:
        try:
            print(f'COM: {fws.get_com_port()}')
            print(f'Infos: {fws.get_device_info()}')
            while True:
                msg = fws.get_device_status()
                print(msg.message)
                if msg.code == 6:
                    break
                    sleep(1)

            fws.wavelength = (532, 10)
            while True:
                msg = fws.get_device_status()
                print(msg.message)
                if msg.code == 6:
                    break
                    sleep(1)

            print(f'Center wl, FWHM: {fws.wavelength}')
        except PolyError as pe:
            print(str(pe))
        finally:
            fws.disconnect()

    
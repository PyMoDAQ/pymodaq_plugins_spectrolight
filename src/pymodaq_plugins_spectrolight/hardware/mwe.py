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
from System import String, Double


path_dll = str(Path(r'C:\FWSPoly'))
sys.path.append(path_dll)
polydll = clr.AddReference('PolyDLL')

from ISM_Device import ClassPoly


if __name__ == '__main__':
    poly = ClassPoly()
    calibration_path = r'C:\FWSPoly\20220818_FAPVIS00222.ism'
    print(f'Connecting: {poly.GetStringMsg(poly.PolyConnect(calibration_path))}')
    try:
        print(f'Status: {poly.GetStringMsg(poly.GetDeviceStatus())}')

        print(f'Enable: {poly.GetDeviceEnabled()}')

        print(f'Setting Wavelength: {poly.GetStringMsg(poly.SetWavelength(532., 10.))}')
        sw, cw, lw, fwhm = '', '', '', ''
        ret, sw, cw, lw, fwhm = poly.GetCurrentWavelength(sw, cw, lw, fwhm)
        print(f'Get Wavelength: {poly.GetStringMsg(ret)}, {cw}, {fwhm}')


    except Exception as e:
        print(e)
    finally:
        print(f'Disconnecting: {poly.GetStringMsg(poly.Disconnect())}')
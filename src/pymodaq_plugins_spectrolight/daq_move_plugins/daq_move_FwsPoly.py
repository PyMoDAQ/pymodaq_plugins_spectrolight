from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main  # common set of parameters for all actuators
from pymodaq.daq_utils.parameter import Parameter

from pymodaq_plugins_spectrolight.hardware.fws_auto import FWSAuto

calib_file_path = r'C:\FWSPoly\20220818_FAPVIS00222.ism'


class DAQ_Move_FwsPoly(DAQ_Move_base):
        """Plugin for the Spectrolight FWS Poly Auto Instrument

        This object inherits all functionality to communicate with PyMoDAQ Module through inheritance via DAQ_Move_base
        It then implements the particular communication with the instrument

        Attributes:
        -----------
        controller: object
            The particular object that allow the communication with the hardware, in general a python wrapper around the
             hardware library
        """
        _controller_units = 'nm'  # here the units is a wavelength in nm
        is_multiaxes = True
        _epsilon = 0.5
        axes_name = ['cw', 'fwhm']
        params = [{'title': 'Calibration file:', 'name': 'calib_path', 'type': 'browsepath', 'value': calib_file_path,
                   'filetype': True},
                  {'title': 'Info:', 'name': 'info', 'type': 'str', 'value': '', 'readonly': True},
                  {'title': 'Status:', 'name': 'status', 'type': 'group', 'children': [
                      {'title': 'cw (nm):', 'name': 'cw', 'type': 'float', 'value': 0.},
                      {'title': 'fwhm (nm):', 'name': 'fwhm', 'type': 'int', 'value': 3, 'min': 3, 'max': 15},]},
                  {'title': 'Blank:', 'name': 'blank', 'type': 'led_push', 'value': False},
                  ] + comon_parameters_fun(is_multiaxes=True, axes_names=axes_name, epsilon=_epsilon)

        def ini_attributes(self):
            self.controller: FWSAuto = None

        def get_actuator_value(self):
            """Get the current value from the hardware with scaling conversion.

            Returns
            -------
            float: The position obtained after scaling conversion.
            """
            cw, fwhm = self.controller.cw_fwhm
            self.settings.child('status', 'cw').setValue(cw)
            self.settings.child('status', 'fwhm').setValue(fwhm)
            if self.settings['multiaxes', 'axis'] == 'cw':
                pos = cw
            else:
                pos = fwhm
            pos = self.get_position_with_scaling(pos)
            return pos

        def close(self):
            """Terminate the communication protocol"""
            self.controller.disconnect()

        def commit_settings(self, param: Parameter):
            """Apply the consequences of a change of value in the detector settings

            Parameters
            ----------
            param: Parameter
                A given parameter (within detector_settings) whose value has been changed by the user
            """
            if param.name() == 'cw':
                self.controller.cw = param.value()
            elif param.name() == 'fwhm':
                self.controller.fwhm = param.value()
            elif param.name() == 'blank':
                if param.value():
                    self.controller.no_filtering()
                else:
                    self.controller.set_cw_fwhm_from_internal()

        def ini_stage(self, controller=None):
            """Actuator communication initialization

            Parameters
            ----------
            controller: (object)
                custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

            Returns
            -------
            info: str
            initialized: bool
                False if initialization failed otherwise True
            """
            self.ini_stage_init(old_controller=controller,
                                new_controller=FWSAuto())
            if self.settings['multiaxes', 'multi_status'] == "Master":
                self.controller.connect(self.settings['calib_path'])

            infos = self.controller.get_device_info()
            range = infos[2]
            cw_min_max = [float(r) for r in range.split('-')]
            self.settings.child('status', 'cw').setOpts(limits=cw_min_max)

            if self.controller.is_device_enabled():
                self.controller.get_device_status()
                self.controller.cw_fwhm = 532., 5.
                initialized = True
            else:
                initialized = False

            info = f'Model: {infos[0]}, Serial: {infos[1]}, Range: {infos[2]}'
            self.settings.child('info').setValue(info)
            return info, initialized

        def move_abs(self, value):
            """ Move the actuator to the absolute target defined by value

            Parameters
            ----------
            value: (float) value of the absolute target positioning
            """
            value = self.check_bound(value)  # if user checked bounds, the defined bounds are applied here
            value = self.round_to_half_integer(value)
            self.target_value = value
            value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
            if self.settings['multiaxes', 'axis'] == 'cw':
                # rounding to closest half integer
                value = self.round_to_half_integer(value)

            setattr(self.controller, self.settings['multiaxes', 'axis'], value)

        @staticmethod
        def round_to_half_integer(value: float):
            return round(value) + round((value - round(value)) * 2) / 2

        def move_rel(self, value):
            """ Move the actuator to the relative target actuator value defined by value

            Parameters
            ----------
            value: (float) value of the relative target positioning
            """
            value = self.check_bound(self.current_position + value) - self.current_position
            self.target_value = value + self.current_position
            value = self.set_position_relative_with_scaling(value)
            self.move_abs(self.target_value)

        def move_home(self):
            """Call the reference method of the controller"""
            pass

        def stop_motion(self):
            """Stop the actuator and emits move_done signal"""
            pass


if __name__ == '__main__':
    main(__file__, init=False)

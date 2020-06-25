#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig module implementation for tpRigToolkits-tools-rigbuilder for Maya
"""

import tpDcc as tp
from tpDcc.libs.python import python

from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import rig


class ControlRig(rig.Rig, object):
    def __init__(self, *args, **kwargs):
        super(ControlRig, self).__init__(*args, **kwargs)

        self._transforms = list()               # List of transforms in the rig module
        self._control_count = 1                 # Number of controls for each rig transform
        self._control_shape_types = dict()      # Stores the shape types for each one of the controls
        self._control_buffers = dict()          # Stores the buffers of each of the controls
        self._create_control_buffers = True     # Stores whether or not control buffer groups should be created

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def transforms(self):
        return self._transforms

    @transforms.setter
    def transforms(self, value):
        self._transforms = value

    @property
    def control_count(self):
        return self._control_count

    @control_count.setter
    def control_count(self, value):
        self._control_count = value

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        if not self._transforms:
            self._transforms = [None]
        self._transforms = python.force_list(self._transforms)

        for transform in self._transforms:
            for i in range(self._control_count):
                description = 'control'
                if i in self._control_descriptions:
                    description = self._control_descriptions[i]
                new_control = self._create_control(description)
                if transform:
                    tp.Dcc.match_translation_rotation(transform, new_control.get())
                if i in self._control_shape_types:
                    new_control.set_curve_type(self._control_shape_types[i])
                if i in self._control_data:
                    new_control.set_data(self._control_data[i])
                if self._create_control_buffers:
                    buffer = self._create_buffer_group(new_control.get())
                    self._control_buffers[new_control.get()] = buffer
                    # tp.Dcc.set_parent(buffer, self._controls_group)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_control_buffer(self, control_name):
        """
        Returns control buffer of the given control (if exists)
        :param control: str
        :return: str
        """

        if not control_name or control_name not in self._control_buffers:
            return None

        return self._control_buffers[control_name]

    def set_create_control_buffers(self, flag):
        """
        Sets whether or not buffer groups should be created for the controls of this rig
        :param flag: bool
        """

        self._create_control_buffers = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_buffer_group(self, control):
        """
        Internal function that creates a new buffer group for the given control
        :param control:
        :return:
        """

        if not self._create_control_buffers:
            return

        control_parsed_name = api.parse_name(control)
        control_description = control_parsed_name.get('description', control.split('_')[0])
        buffer_name = api.solve_name('buffer', control_description)

        return tp.Dcc.create_buffer_group(control, buffer_name=buffer_name)

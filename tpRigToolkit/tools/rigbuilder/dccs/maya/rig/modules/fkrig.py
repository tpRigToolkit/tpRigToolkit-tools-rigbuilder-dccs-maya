#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains FK rig implementations for tpRigToolkit-tools-rigbuilder for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya

from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import joint as rig_joint


class FkRig(rig_joint.BufferRig, object):
    """
    Module to setup FK rigs (such as fingers or arms):
        - One FK control for each joint will be created
        - FK chain is created following list of joints order
    """

    def __init__(self, *args, **kwargs):

        self._control = ''                                      # First control in the FK chain of controls
        self._last_control = ''                                 # Last control in the FK chain of controls
        self._skip_controls = list()                            # List of controls to skip during FK chain setup
        self._match_to_rotation = True                          # Sets if Fk controls must match driver joint rotation
        self._offset_rotation = list()                          # List of offset rotations for all FK chain controls
        self._offset_rotation_index = dict()                    # Dict of offset rotation for specific FK chain controls

        self._current_control_index = 0                            # Internal index used in the FK chain building setup
        self._transforms_list = list()                          # Internal list used during the FK chain building setup
        self._current_buffer_group = None                       # Internal var that stores buffer group during setup

        super(FkRig, self).__init__(*args, **kwargs)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        """
        Overrides default creation of the rig. Rig attributes must be set before running this function
        """

        super(FkRig, self).create()

        self._setup(self._buffer_joints)

    def _create_control(self, *args, **kwargs):
        """
        Overrides internal function that creates a new control for current rig
        :param args:
        :param kwargs:
        :return: RigControl
        """

        new_control = super(FkRig, self)._create_control(*args, **kwargs)

        sub = kwargs.get('sub', False)
        if not sub:
            self._last_control = self._control
            self._control = new_control

        self._set_control_attributes(new_control)

        buffer_group = tp.Dcc.create_buffer_group(new_control.get())

        if not sub:
            self._current_buffer_group = buffer_group

        self._controls_dict[new_control.get()]['buffer'] = buffer_group

        if not sub:
            pass

        return new_control

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_skip_controls(self, increment_list):
        """
        Sets which controls are skipped
        :param increment_list: list(int), list of controls indexes starting from 0 (first control)
        """

        self._skip_controls = increment_list

    def set_match_to_rotation(self, flag):
        """
        Sets whether or not controls must match orientation of driven nodes (usually joints)
        :param flag: bool
        """

        self._match_to_rotation = flag

    def set_offset_rotation(self, value_list):
        """
        Set offset rotations for each FK chain control
        For example, [90, 0, 90] will rotate buffer group of each control 90 degrees in X and Z axes
        :param value_list: list(float, float, float), list of offset rotation vectors
        """

        self._offset_rotation = value_list

    def set_offset_rotation_at_index(self, control_index, value_list):
        """
        Set offset rotations for a specific FK chain control
        For example, [90, 0, 90] will rotate buffer group of each control 90 degrees in X and Z axes
        :param control_index: int, index of the control to set offset rotation of
        :param value_list: list(float, float, float), list of offset rotation vectors
        """

        self._offset_rotation[control_index] = value_list

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _set_control_attributes(self, control):
        """
        Internal function that is called for each of the controls in the FK chain and it is used to setup custom
        attributes in the FK chain controls
        :param control: RigControl
        """

        control.hide_scale_attributes()

    def _attach(self, control, target_transform):
        """
        Internal callback function that attaches given control to given transform
        :param control: str, control to attach to a specific transform (usually a joint)
        :param target_transform: str, name of the transform that will be attached to the control
        """

        if not self._attach_chain:
            return

        if self._create_sub_controls:
            control = self._controls_dict[control]['subs'][-1]

        control_buffer = None
        if 'buffer' in self._controls_dict[control]:
            control_buffer = self._controls_dict[control]['buffer']
        if control_buffer:
            offset_rotation = None
            if self._offset_rotation:
                offset_rotation = self._offset_rotation
            if self._current_control_index in self._offset_rotation_index:
                offset_rotation = self._offset_rotation_index[self._current_control_index]
            if offset_rotation:
                tp.Dcc.rotate_node_in_object_space(control_buffer, offset_rotation)

        tp.Dcc.create_parent_constraint(target_transform, control, maintain_offset=True)

    def _setup(self, transforms):
        """
        Internal function that setup the FK chain
        :param transforms: list(str)
        """

        found_to_skip = list()

        if self._skip_controls:
            for ctrl_index in self._skip_controls:
                found_xform = None
                try:
                    found_xform = transforms[ctrl_index]
                except Exception:
                    pass
                if found_xform:
                    found_to_skip.append(found_xform)

        self._current_control_index = 0
        for i in range(len(transforms)):
            if transforms[i] in found_to_skip:
                self._current_control_index += 1
                continue

            self._current_control_index = i
            control_data = self._control_data.get(self._current_control_index, dict())
            control_description = self._control_descriptions.get(self._current_control_index, 'control')
            new_control = self._create_control(
                control_description, control_data=control_data, id=self._current_control_index)
            new_control = new_control.get()
            self._setup_increment(new_control, transforms)

    def _setup_increment(self, control, transforms):
        """
        Internal function that is called during the FK chain building process.
        This function is called for each control that is created for the FK chain
        :param control: str, name of the control in the FK chain
        :param transforms: list(str), list of transforms (usually joints) of the FK chain
        """

        self._transforms_list = transforms
        current_xform = transforms[self._current_control_index]

        self._setup_all_controls(control, current_xform)

        if self._current_control_index == 0:
            self._setup_first_control(control, current_xform)
        if self._current_control_index == (len(transforms) - 1):
            self._setup_last_control(control, current_xform)
        if self._current_control_index > 0:
            self._setup_control_greater_than_first(control, current_xform)
        if self._current_control_index < len(transforms):
            self._setup_control_lower_than_last(control, current_xform)
        if len(transforms) > self._current_control_index > 0:
            self._setup_control_lower_than_last_and_greater_than_first(control, current_xform)
        if self._current_control_index == (len(transforms) - 1) or self._current_control_index == 0:
            self._setup_first_or_last_control(control, current_xform)

    def _setup_all_controls(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called once for each control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        control_buffer = self._controls_dict[control]['buffer']
        if self._match_to_rotation:
            tp.Dcc.match_rotation(current_transform, control_buffer)

        tp.Dcc.match_translation(current_transform, control_buffer)
        tp.Dcc.match_scale(current_transform, control_buffer)
        tp.Dcc.match_translation_to_rotate_pivot(current_transform, control_buffer)

    def _setup_first_control(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the first control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        self._attach(control, current_transform)

    def _setup_last_control(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the last control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _setup_control_greater_than_first(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for all the controls in the FK chain that are not the first one.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        self._attach(control, current_transform)

        if self._create_sub_controls:
            last_control = self._controls_dict[self._last_control.get()]['subs'][-1]
            tp.Dcc.set_parent(self._controls_dict[control]['buffer'], last_control)
            if tp.is_maya():
                maya.cmds.controller(control, last_control, p=True)
        else:
            if self._last_control:
                tp.Dcc.set_parent(self._controls_dict[control]['buffer'], self._last_control.get())
                if tp.is_maya():
                    maya.cmds.controller(control, self._last_control.get(), p=True)

    def _setup_control_lower_than_last(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the FK chain controls that are lower than the last control
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _setup_control_lower_than_last_and_greater_than_first(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the FK chain controls that are lower than the last control and are not the first one
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _setup_first_or_last_control(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the FK chain first and last controls.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains FK rig implementations for tpRigToolkit-tools-rigbuilder for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp

from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import joint as rig_joint

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import ik, rig as rig_utils


class IkLimbRig(rig_joint.BufferRig, object):
    """
    Module to setup Ik limb rigs
    """

    def __init__(self, *args, **kwargs):
        super(IkLimbRig, self).__init__(*args, **kwargs)

        self._top_control = None                            # Top control of the limb rig
        self._sub_control = None                            # Sub control of the limb rig
        self._bottom_control = None                         # Bottom control of the limb rig
        self._pole_vector_control = None                    # Pole vector control of the limb rig Ik handle
        self._pole_vector_constraint = None                 # Pole vector constraint used by the limb rig Ik
        self._build_top_control = True                      # Whether to create top control or not
        self._top_control_as_locator = False                # Whether to create top control as a curve or as a locator
        self._ik_handle = None                              # IK handle used by limb rig
        self._right_side_fix = True                         # Whether or not fix orientation on right side IK limbs
        self._ik_chain = list()                             # List of joints that forms IK chain
        self._duplicate_chain_replace = ['joint', 'ik']     # List containing the replace strings for the new joints
        self._negate_right_scale = False                    # Whether or not negate scale right control values
        self._negate_right_scale_values = [-1, -1, -1]      # Negate scale values used in the negate right controls
        self._ik_buffer_joint = True                        # Whether ik buffer joint should be created or not
        self._pole_vector_control_offset = 3                # Distance pole vector control is offset from mid joint
        self._pole_vector_control_offset_locator = None     # Sets the name of the locator pole vector will be snap
        self._pole_vector_buffer = None                     # Buffer group used for pole vector control
        self._pole_angle_joints = list()                    # List of joints used to define pole vector angle
        self._build_pole_vector_control = True              # Whether create or not pole vector control for Ik handle
        self._pole_vector_control_data = None               # Pole vector control data used to build the control
        self._top_control_data = None                       # Top control data used to build the control
        self._bottom_control_data = None                    # Bottom control data used to build the control
        self._match_bottom_control_to_joint = True          # Whether or not bottom control matches last joint rotation
        self._orient_constraint = True                      # Whether or not end effector controls ik handle rotation
        self._create_sub_control = True                     # Whether create sub control or not

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        """
        Overrides base Rig create function
        """

        super(IkLimbRig, self).create()

        if self._build_top_control:
            self._create_top_control()
        else:
            self._top_control = tp.Dcc.create_locator('locator_top_{}'.format(self._get_name()))
            tp.Dcc.match_translation_rotation(self._joints[0], self._top_control)
        self._create_top_control_buffer()
        self._create_pole_vector_control()
        self._create_bottom_control()
        self._create_bottom_control_buffer()

        if self._build_pole_vector_control:
            self._create_pole_vector()

        if tp.is_maya():
            if self._build_pole_vector_control:
                if self._build_top_control:
                    maya.cmds.controller(self._pole_vector_control, self._top_control, p=True)
                    maya.cmds.controller(self._bottom_control, self._pole_vector_control, p=True)
            else:
                if self._build_top_control:
                    maya.cmds.controller(self._bottom_control, self._top_control, p=True)

    def _create_before_attach_joints(self):
        """
        Overrides base _create_before_attach_joints function
        Internal function that is called before attaching duplicated joints to the original chain
        """

        super(IkLimbRig, self)._create_before_attach_joints()

        self._create_ik_handle()

    def _duplicate_joints(self):
        """
        Overrides base _duplicate_joints function
        Internal function that duplicates the original joints of the buffer rig
        :return: list(str), list of new duplicated joints
        """

        super(IkLimbRig, self)._duplicate_joints()

        # tp.Dcc.duplicate_hierarchy(
        #     self._joints[0], stop_at=self._joints[-1],
        #     replace_str=self._duplicate_chain_replace[0], new_str=self._duplicate_chain_replace[1])

        self._ik_chain = self._buffer_joints

        if self._create_buffer_joints:
            ik_group = self._create_group('ik')
            tp.Dcc.set_parent(self._ik_chain[0], ik_group)
            tp.Dcc.set_parent(ik_group, self._setup_group)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_create_top_control(self, flag):
        """
        Sets whether or not top control for Ik limb rig setup should be created
        :param flag: bool
        """

        self._build_top_control = flag

    def set_top_control_as_locator(self, flag):
        """
        Sets whether or not top control should be a locator or a proper control
        :param flag: bool
        """

        self._top_control_as_locator = flag

    def set_right_side_fix(self, flag):
        """
        Sets whether or not right side orientation should be compensated
        :param flag: bool
        """

        self._right_side_fix = flag

    def set_negate_right_scale(self, flag, scale_x=-1, scale_y=-1, scale_z=-1):
        """
        Negatives the of scale of right side controls (mirror) to make them better for cycles
        :param flag: bool
        :param scale_x: float
        :param scale_y: float
        :param scale_z: float
        """

        self._negate_right_scale = flag
        self._negate_right_scale_values = [scale_x, scale_y, scale_z]

    def set_create_ik_buffer_joint(self, flag):
        """
        Sets whether or not a buffer should be created in the end IK joint (usually wrist or elbow)
        Used to fix IK offset problems while Ik limb stretching.
        :param flag: bool
        :return:
        """

        self._ik_buffer_joint = flag

    def set_create_pole_vector_control(self, flag):
        """
        Whether to create or not a control to manage Ik handle pole vector
        :param flag: bool
        """

        self._build_pole_vector_control = flag

    def set_pole_vector_control_data(self, control_data_dict):
        """
        Sets the control data used to create the pole vector control
        :param control_data_dict: dict
        """

        self._pole_vector_control_data = control_data_dict

    def set_top_control_data(self, control_data_dict):
        """
        Sets the control data used to create the top control
        :param control_data_dict: dict
        """

        self._top_control_data = control_data_dict

    def set_bottom_control_data(self, control_data_dict):
        """
        Sets the control data used to create the bottom control
        :param control_data_dict: dict
        """

        self._bottom_control_data = control_data_dict

    def set_orient_constraint(self, flag):
        """
        Sets whether or not the end effector should control the orientation of the Ik handle
        :param flag: bool
        """

        self._orient_constraint = flag

    def set_create_sub_control(self, flag):
        """
        Sets whether or not ik limb rig sub control should be created
        :param flag: bool
        """

        self._create_sub_control = flag

    def set_pole_vector_control_offset(self, value):
        """
        Sets the amount of distance the pole vector control should offset from the mid Ik chain joint
        :param value: float
        """

        self._pole_vector_control_offset = value

    def set_pole_angle_joints(self, joints):
        """
        Sets the joints the pole angle is calculated from
        :param joints: list(str)
        """

        self._pole_angle_joints = joints

    # ==============================================================================================
    # PRIVATE
    # ==============================================================================================

    def _create_top_control(self):
        """
        Internal function that creates top control of the Ik limb rig setup
        :return: str
        """

        if self._top_control_as_locator:
            self._top_control = tp.Dcc.create_locator('locator_{}'.format(self._get_name()))
        else:
            new_control = self._create_control('top', control_data=self._top_control_data)
            new_control.hide_scale_and_visibility_attributes()
            self._top_control = new_control.get()

        return self._top_control

    def _create_bottom_control(self):
        """
        Internal function that creates bottom control of the Ik limb rig setup
        :return: str
        """

        new_control = self._create_control('bottom', control_data=self._bottom_control)
        new_control.hide_scale_and_visibility_attributes()
        self._bottom_control = new_control.get()
        self._fix_right_side_orient(self._bottom_control)

        if self._create_sub_control:
            sub_control = self._create_control('bottom', sub=True)
            sub_control.hide_scale_and_visibility_attributes()
            sub_control_buffer = tp.Dcc.create_buffer_group(sub_control.get())
            self._sub_control = sub_control.get()
            tp.Dcc.set_parent(sub_control_buffer, self._bottom_control)
            self._connect_sub_visibility('{}.subVisibility'.format(self._bottom_control), self._sub_control)

        return self._bottom_control

    def _create_top_control_buffer(self):
        """
        Internal function that creates the buffer group for the top control of the Ik limb rig setup
        """

        tp.Dcc.match_translation_rotation(self._ik_chain[0], self._top_control)
        self._fix_right_side_orient(self._top_control)
        xform_group = tp.Dcc.create_buffer_group(self._top_control)
        if self._negate_right_scale and tp.Dcc.name_is_right(self._side):
            for i, axis in enumerate('XYZ'):
                tp.Dcc.set_attribute_value(xform_group, 'scale{}'.format(axis), self._negate_right_scale_values[i])

        tp.Dcc.create_parent_constraint(self._ik_chain[0], self._top_control, maintain_offset=True)

    def _create_bottom_control_buffer(self):
        """
        Internal function that creates the buffer group for the bottom control of the Ik limb rig setup
        """

        if self._match_bottom_control_to_joint:
            tp.Dcc.match_translation_rotation(self._ik_chain[-1], self._bottom_control)
        else:
            tp.Dcc.match_translation(self._ik_chain[-1], self._bottom_control)
        self._fix_right_side_orient(self._bottom_control)

        buffer_group = tp.Dcc.create_buffer_group(self._bottom_control)
        driver_group = tp.Dcc.create_buffer_group(self._bottom_control, suffix='driver')

        if self._negate_right_scale and tp.Dcc.name_is_right(self._side):
            for i, axis in enumerate('XYZ'):
                tp.Dcc.set_attribute_value(buffer_group, 'scale', self._negate_right_scale_values[i])

        ik_handle_parent = tp.Dcc.node_parent(self._ik_handle)

        if self._sub_control:
            tp.Dcc.set_parent(ik_handle_parent, self._sub_control)
        else:
            tp.Dcc.set_parent(ik_handle_parent, self._bottom_control)

        if self._orient_constraint:
            if self._sub_control:
                tp.Dcc.create_orient_constraint(self._ik_chain[-1], self._sub_control, maintain_offset=True)
            else:
                tp.Dcc.create_orient_constraint(self._ik_chain[-1], self._bottom_control, maintain_offset=True)

    def _create_pole_vector_control(self):
        """
        Internal function that creates control that manages Ik handle
        """

        if self._build_pole_vector_control:
            self._pole_vector_control = self._create_control(
                'poleVector', curve_type='cube', control_data=self._pole_vector_control_data)
            if self._use_side_colors:
                if self._set_sub_control_color_only:
                    self._pole_vector_control.set_color(api.get_color_of_side(self._side, sub_color=True))
                else:
                    self._pole_vector_control.set_color(api.get_color_of_side(self._side, sub_color=False))

            self._pole_vector_control.hide_scale_and_visibility_attributes()

    def _create_pole_vector(self):
        control = self._pole_vector_control
        self._pole_vector_control = self._pole_vector_control.get()

        tp.Dcc.add_title_attribute(self._bottom_control, 'POLE_VECTOR')
        tp.Dcc.add_bool_attribute(self._bottom_control, 'poleVisibility')
        tp.Dcc.add_integer_attribute(self._bottom_control, 'twist')
        if tp.Dcc.name_is_left(self._side):
            tp.Dcc.connect_attribute(self._bottom_control, 'twist', self._ik_handle, 'twist')
        else:
            tp.Dcc.connect_multiply(self._bottom_control, 'twist', self._ik_handle, 'twist', value=-1)

        pole_joints = self._get_pole_joints()

        pole_vector_position = tp.Dcc.get_pole_vector_position(
            pole_joints[0], pole_joints[1], pole_joints[2], offset=self._pole_vector_control_offset)
        tp.Dcc.move_node(control.get(), pole_vector_position[0], pole_vector_position[1], pole_vector_position[2])

        self._create_pole_vector_constraint()

        pole_vector_buffer_group = tp.Dcc.create_buffer_group(control.get())

        name = self._get_name('poleVectorLine')
        rig_line = rig_utils.RiggedLine(pole_joints[1], control.get(), name).create()
        tp.Dcc.set_parent(rig_line, self._controls_group)

        tp.Dcc.connect_attribute(self._bottom_control, 'poleVisibility', pole_vector_buffer_group, 'visibility')
        tp.Dcc.connect_attribute(self._bottom_control, 'poleVisibility', rig_line, 'visibility')

        self._pole_vector_buffer = pole_vector_buffer_group

    def _create_pole_vector_constraint(self):
        """
        Internal function that creates the pole vector constraint used by the Ik limb rig
        """

        self._pole_vector_constraint = tp.Dcc.create_pole_vector_constraint(self._pole_vector_control, self._ik_handle)

    def _get_pole_joints(self):
        """
        Returns all joints used to setup pole vector angle
        :return: list(str)
        """

        if not self._pole_angle_joints:
            mid_joint_index = int(len(self._ik_chain) / 2)
            mid_joint = self._ik_chain[mid_joint_index]
            joints = [self._ik_chain[0], mid_joint, self._ik_chain[-1]]

            return joints

        return self._pole_angle_joints

    def _fix_right_side_orient(self, control):
        """
        Internal function that fixes right side control to reverse orientation on YZ channels
        :param control: str, name of the control we want to fix orient of
        """

        if not self._right_side_fix or not tp.Dcc.name_is_right(side=self._side):
            return

        xform_locator = tp.Dcc.create_locator()
        tp.Dcc.match_translation_rotation(control, xform_locator)

        buffer_group = tp.Dcc.create_buffer_group(xform_locator)
        tp.Dcc.set_attribute_value(xform_locator, 'rotateY', 180)
        tp.Dcc.set_attribute_value(xform_locator, 'rotateZ', 180)
        tp.Dcc.match_translation_rotation(xform_locator, control)

        tp.Dcc.delete_object(buffer_group)

    def _create_buffer_joint(self):
        """
        Internal function that creates a buffer joint on top of the end joint of the Ik chain
        The scale of this buffer is connected to the inverseScale of the child joint
        :return: str, new created buffer joint
        """

        buffer_joint = tp.Dcc.duplicate_object(self._ik_chain[-1], only_parent=True)
        tp.Dcc.set_parent(self._ik_chain[-1], buffer_joint)
        if not tp.Dcc.is_attribute_connected_to_attribute(buffer_joint, 'scale', self._ik_chain[-1], 'inverseScale'):
            tp.Dcc.connect_attribute(buffer_joint, 'scale', self._ik_chain[-1], 'inverseScale')

        for axis in 'XYZ':
            for attr_name in ['rotate', 'jointOrient']:
                tp.Dcc.set_attribute_value(self._ik_chain[-1], '{}{}'.format(attr_name, axis), 0)

        return buffer_joint

    def _create_ik_handle(self):
        """
        Internal function that creates the Ik handle for the Ik limb rig
        :return:
        """

        if self._ik_buffer_joint:
            buffer_joint = self._create_buffer_joint()
        else:
            buffer_joint = self._ik_chain[-1]

        ik_solver = ''
        if tp.is_maya():
            ik_solver = ik.IkHandle.SOLVER_RP
        self._ik_handle = tp.Dcc.create_ik_handle(
            self._get_name('ikHandle'), start_joint=self._ik_chain[0], end_joint=buffer_joint, solver_type=ik_solver)
        ik_handle_buffer = tp.Dcc.create_buffer_group(self._ik_handle)
        tp.Dcc.set_parent(ik_handle_buffer, self._setup_group)
        tp.Dcc.hide_node(ik_handle_buffer)

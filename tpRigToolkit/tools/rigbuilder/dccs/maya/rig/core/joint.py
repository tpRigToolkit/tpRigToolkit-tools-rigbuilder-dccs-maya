#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base joint rig implementations for tpRigBuilderMaya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.libs.python import python

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import rig
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.utils import rigswitch


class JointRig(rig.Rig, object):

    """
    Adds attaching joint buffer chain functionality
    """

    ATTACH_TYPE_CONSTRAINT = 0
    ATTACH_TYPE_MATRIX = 1

    def __init__(self, description, side=None):
        super(JointRig, self).__init__(description, side)

        self._joints = list()
        self._attach_joints = True                      # Defines if joint attaching is enabled or not
        self._auto_control_visibility = True            # Defines whether or not, when attaching, the control group
        #                                                 visibility is attached to the switch attribute of the
        #                                                 first joint
        self._switch_shape_attribute_name = None
        self._attach_type = 0                           # Defines the attach type

    @property
    def attach_joints(self):
        return self._attach_joints

    @attach_joints.setter
    def attach_joints(self, value):
        self._attach_joints = value

    @property
    def attach_type(self):
        return self._attach_type

    @attach_type.setter
    def attach_type(self, value):
        self._attach_type = value

    @property
    def auto_switch_visibility(self):
        return self._auto_control_visibility

    @auto_switch_visibility.setter
    def auto_switch_visibility(self, flag):
        self._auto_control_visibility = flag

    def set_joints(self, joints):
        """
        Sets the joints that the joint rig should work on
        :param joints: list(str), list of joint names
        """

        joints = python.force_list(joints)
        self._joints = joints
        self._buffer_joints = joints
        self._check_joints(self._joints)

    def set_add_switch_shape(self, name_for_attribute, name_for_node=None):
        """
        Adds a switch attribute
        :param name_for_attribute: str, name to give to the switch attribute
        :param name_for_node: str, name to give the shape to be created that attribute will be located in
        """

        self._switch_shape_attribute_name = name_for_attribute
        self._switch_shape_node_name = name_for_node

    def _check_joints(self, joints):
        for jnt in joints:
            if tp.Dcc.node_is_joint(jnt) or tp.Dcc.node_is_transform(jnt):
                continue
            tpRigToolkit.logger.warning(
                '{} is not a joint or transform. {} may not be build properly'.format(jnt, self.__class__.__name__))

    def _setup_attach_joints(self, source_chain, target_chain):
        if not self._attach_joints:
            return

        tp.Dcc.attach_joints(source_chain, target_chain, attach_type=self._attach_type)

        if tp.Dcc.attribute_exists(target_chain[0], 'switch'):
            switch = rigswitch.RigSwitch(target_chain[0])
            weight_count = switch.get_weight_count()
            if weight_count > 0:
                if self._auto_control_visibility:
                    switch.add_groups_to_index(weight_count - 1, self._control_group)
                switch.create()


class BufferRig(JointRig, object):
    """
    Extends JointRig with the ability to create buffer joint chains
    The buffer chain creates a duplicate chain for attaching the setup to the main chain
    This allows multiple rigs to be attached to the main chain
    """

    def __init__(self, name, side=None):
        super(BufferRig, self).__init__(name, side)

        self._buffer_joints = list()
        self._create_buffer_joints = False
        self._build_hierarchy = False
        self._buffer_replace = ['joint', 'buffer']

    def set_buffer_replace(self, replace_this, with_this):
        self._buffer_replace = [replace_this, with_this]

    def set_build_hierarchy(self, flag):
        self._build_hierarchy = flag

    def create(self):
        super(BufferRig, self).create()
        self._duplicate_joints()
        self._create_before_attach_joints()
        if self._create_buffer_joints:
            self._setup_attach_joints(self._buffer_joints, self._joints)

    def delete_setup(self):
        if self._create_buffer_joints:
            tpRigToolkit.logger.warning(
                'Skipping setup group deletion. The buffer is set to True and duplicate '
                'joints need to be stored under setup group')
            return
        super(BufferRig, self).delete_setup()

    def set_buffer(self, flag, name_for_attribute=None, name_for_node=None):
        """
        Enables/Disables the creation of the buffer chain
        :param flag: bool, Whether or not to create the buffer chain
        :param name_for_attribute: str, name to give an optional switch attribute
        :param name_for_node: str, name to give the node where the attribute lives on
        """

        self._create_buffer_joints = flag
        self._connect_important = flag
        if name_for_attribute:
            self._switch_shape_attribute_name = name_for_attribute
            self._switch_shape_node_name = name_for_node

    def _duplicate_joints(self):
        if self._create_buffer_joints:
            if self._build_hierarchy:
                self._buffer_joints = tp.Dcc.create_hierarchy(
                    transforms=self._joints, replace_str=self._buffer_replace[0], new_str=self._buffer_replace[1])
            else:
                self._buffer_joints = tp.Dcc.duplicate_hierarchy(
                    self._joints, stop_at=self._joints[-1], force_only_these=self._joints,
                    replace_str=self._buffer_replace[0], new_str=self._buffer_replace[1])
            tp.Dcc.set_parent(self._buffer_joints[0], self._setup_group)
        else:
            self._buffer_joints = self._joints

        return self._buffer_joints

    def _create_before_attach_joints(self):
        return

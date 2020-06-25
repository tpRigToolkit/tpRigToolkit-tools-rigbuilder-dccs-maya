#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base joint rig implementations for tpRigToolkit-tools-rigbuilder for Maya
"""

import tpDcc as tp
from tpDcc.libs.python import python
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import joint as joint_utils, rig as rig_utils, shape as shape_utils

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import rig


class JointRig(rig.Rig, object):
    """
    Rig component that allows the attachment of joint buffer chains
    """

    ATTACH_TYPE_CONSTRAINT = 0
    ATTACH_TYPE_MATRIX = 1

    def __init__(self, *args, **kwargs):
        super(JointRig, self).__init__(*args, **kwargs)

        self._joints = list()                               # List of joints of the joint rig component
        self._attach_chain = True                           # Indicates if chain joints will be attached to other chain
        self._attach_type = self.ATTACH_TYPE_CONSTRAINT     # Indicates the type of attachment

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def joints(self):
        return self._joints

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def _post_create_messages(self):
        """
        Internal function that is called during post create function
        Creates custom messages to rig controls group
        """

        super(JointRig, self)._post_create_messages()

        self._post_create_message('_joints', 'joint')

        if self._joints:
            tp.Dcc.connect_message_attribute(self._controls_group, self._joints[0], 'rig1')

        self._post_store_orig_matrix('joints')

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_joints(self, joints):
        """
        Sets the joints that the joint rig should work on
        :param joints: list(str), list of joint names
        """

        joints = python.force_list(joints)

        self._check_joints(joints)

        self._joints = joints

    def set_enable_attach_joints(self, flag):
        """
        Sets whether or not joints should be attached
        :param flag: bool
        """

        self._attach_chain = flag

    def set_attach_type(self, attach_type):
        """
        Sets which attach type is used in case joints are attached
        :param attach_type: int (ATTACH_TYPE_CONSTRAINT = 0; ATTACH_TYPE_MATRIX = 1)
        """

        self._attach_type = attach_type

    def set_create_switch(self, flag):
        """
        Sets whether or not create switch functionality should be executed or not
        :param flag: bool
        """

        self._create_switch = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _check_joints(self, joints):
        """
        Internal function that checks if given joints are valid joints for current rig or not
        :param joints: list(str), list of joints to check
        """

        for jnt in joints:
            if tp.Dcc.node_is_joint(jnt) or tp.Dcc.node_is_transform(jnt):
                continue
            raise Exception('{} is not a joint or transform'.format(jnt))


class BufferRig(JointRig, object):
    """
    Extends JointRig with the ability to create buffer joint chains
    The buffer chain creates a duplicate chain for attaching the setup to the main chain
    This allows multiple rigs to be attached to the main chain
    """

    def __init__(self, *args, **kwargs):
        super(BufferRig, self).__init__(*args, **kwargs)

        self._buffer_joints = list()
        self._create_buffer_joints = False                  # Sets whether or not original joints should be duplicated
        self._build_hierarchy = False
        self._create_switch = False                         # Indicates whether switch functionality should work
        self._switch_shape_attribute_name = None            # Attribute name for switch functionality
        self._switch_shape_node_name = None                 # Node that contains switch functionality
        self._auto_switch_visibility = True                 # Sets if control vis will be handle by first joint attr
        self._switch_parent = None                          # Parent node that contains switch functionality
        self._switch_attribute_name = 'switch'              # Defines the name of the attribute that handle switch
        self._buffer_replace = ['joint', 'buffer']          # List containing the replace strings for the new joints

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def buffer_joints(self):
        return self._buffer_joints

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def set_joints(self, joints):
        super(BufferRig, self).set_joints(joints)

        self._buffer_joints = joints

    def create(self):
        """
        Overrides base JointRig create function
        """

        super(BufferRig, self).create()

        self._duplicate_joints()

        self._create_before_attach_joints()

        if self._create_buffer_joints:
            self._attach_joints(self._buffer_joints, self._joints)

    def delete_setup(self):
        """
        Overrides base JointRig delete setup
        """

        if self._create_buffer_joints:
            tpRigToolkit.logger.warning(
                'Skipping setup group deletion. Buffer creation is set to True and duplicated '
                'joints need to be stored under that group')
            return

        super(BufferRig, self).delete_setup()

    def _post_create(self):
        """
        Internal function that is created after the rig is created
        """

        super(JointRig, self)._post_create()

        self._post_add_shape_switch()
        self._post_connect_controls_to_switch_parent()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_buffer(self, flag, name_for_switch_attribute=None, name_for_switch_node=None):
        """
        Sets whether or not buffer chain should be created
        :param flag: bool
        :param name_for_switch_attribute: str
        :param name_for_switch_node: str
        """

        self._create_buffer_joints = flag
        self._connect_messages = flag

        if name_for_switch_attribute:
            self._switch_shape_attribute_name = name_for_switch_attribute
            self._switch_shape_node_name = name_for_switch_node

    def set_buffer_replace(self, original_string, new_string):
        """
        Sets the strings that will be used when renaming the buffer joints
        :param original_string: str
        :param new_string: str
        """

        self._buffer_replace = [original_string, new_string]

    def set_build_hierarchy(self, flag):
        """
        Sets whether or not buffer joint hierarchy should be duplicated or build from scratch
        :param flag: bool
        """

        self._build_hierarchy = flag

    def set_auto_switch_visibility(self, flag):
        """
        Sets whether or not, when attaching more than one joint chain, control group visibility will be managed
        by an attribute added to the first joint.
        :param flag: bool
        """

        self._auto_switch_visibility = flag

    def set_switch_parent(self, value):
        """
        Sets node name that stores switch parent functionality
        :param value: str
        """

        self._switch_parent = value

    def set_add_switch_shape(self, attr_name, node_name=None):
        """
        Adds a switch attribute for the buffer attach functionality (for example, Fk/Ik)
        :param attr_name: str, name to give to the switch attribute during the creation of the switch functionality.
        :param node_name: str, name to give to the shape to be created where switch attribute will live on.
        """

        self._switch_shape_attribute_name = attr_name
        self._switch_shape_node_name = node_name

    def set_switch_attribute_name(self, attr_name):
        """
        Sets the attribute name that handles switch functionality
        :param attr_name: str
        """

        self._switch_attribute_name = attr_name

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_before_attach_joints(self):
        """
        Internal function that is called before attaching duplicated joints to the original chain
        """

        return

    def _duplicate_joints(self):
        """
        Internal function that duplicates the original joints of the buffer rig
        :return: list(str), list of new duplicated joints
        """

        if self._create_buffer_joints:
            if self._build_hierarchy:
                build_hierarchy = joint_utils.BuildJointHierarchy()
                build_hierarchy.set_transforms(self._joints)
                build_hierarchy.set_replace(self._buffer_replace[0], self._buffer_replace[1])
                self._buffer_joints = build_hierarchy.create()
            else:
                self._buffer_joints = tp.Dcc.duplicate_hierarchy(
                    self._joints, stop_at=self._joints[-1], force_only_these=self._joints,
                    replace_str=self._buffer_replace[0], new_str=self._buffer_replace[1])

            # Duplicated joints are stored in the setup group
            tp.Dcc.set_parent(self._buffer_joints[0], self._setup_group)

        return self._buffer_joints

    def _attach_joints(self, source_chain, target_chain):
        """
        Internal function that attaches source chain into given target chain
        :param source_chain: list(str)
        :param target_chain: list(str)
        :return: bool
        """

        if not self._attach_chain:
            return False

        tp.Dcc.attach_joints(
            source_chain=source_chain, target_chain=target_chain, attach_type=self._attach_type,
            create_switch=self._create_switch, switch_attribute_name=self._switch_attribute_name)

        if self._create_switch:
            if tp.Dcc.attribute_exists(target_chain[0], self._switch_attribute_name):
                switch = rig_utils.RigSwitch(target_chain[0])
                weight_count = switch.get_weight_count()
                if weight_count > 0:
                    if self._auto_switch_visibility:
                        switch.add_groups_to_index(weight_count - 1, self._controls_group)
                    switch.create()

        return True

    def _post_add_shape_switch(self):
        if not self._create_buffer_joints or not self._switch_shape_attribute_name or not self._create_switch:
            return

        shapes = shape_utils.get_shapes_of_type(self._joints[0], shape_type='locator', no_intermediate=True)

        name = self._switch_shape_attribute_name
        node_name = '{}_setting'.format(self._switch_attribute_name)
        if self._switch_shape_attribute_name:
            node_name = self._switch_shape_node_name
        else:
            if self._switch_shape_attribute_name:
                node_name = self._switch_shape_attribute_name

        if tp.Dcc.object_exists(node_name) and tp.Dcc.node_is_a_shape(node_name):
            shapes = [node_name]

        if not shapes:
            locator = tp.Dcc.create_locator()
            locator_shape = tp.Dcc.list_shapes(locator)
            shapes = shape_utils.get_shapes_of_type(locator_shape, shape_type='locator', no_intermediate=True)
            for axis in 'XYZ':
                tp.Dcc.set_attribute_value(shapes[0], 'localScale{}'.format(axis), 0)

            tp.Dcc.hide_attributes(shapes[0], ['localPosition', 'localScale'])
            shapes = maya.cmds.parent(shapes[0], self._joints[0], relative=True, shape=True)
            tp.Dcc.delete_object(locator)
            shapes[0] = tp.Dcc.rename_node(shapes[0], tp.Dcc.find_unique_name(node_name))

        joint_shape = shapes[0]

        if not tp.Dcc.attribute_exists(joint_shape, name):
            tp.Dcc.add_integer_attribute(joint_shape, name, keyable=True, min_value=0)
        if not tp.Dcc.is_attribute_connected(self._joints[0], self._switch_attribute_name):
            tp.Dcc.connect_attribute(joint_shape, name, self._joints[0], self._switch_attribute_name)

        max_value = tp.Dcc.attribute_query(self._joints[0], name, max=True)
        try:
            test_max = tp.Dcc.attribute_query(joint_shape, name, max=True)
            max_value = test_max if max_value < test_max else max_value
        except Exception:
            pass

        tp.Dcc.add_integer_attribute(joint_shape, name, max_value=max_value, default_value=max_value)
        for ctrl in self.controls:
            maya.cmds.parent(shapes[0], ctrl, add=True, shape=True)
        tp.Dcc.connect_message_attribute(shapes[0], self._controls_group, self._switch_attribute_name)

    def _post_connect_controls_to_switch_parent(self):
        if not self._switch_parent or not self._create_switch:
            return

        controls = self.get_all_controls()
        for ctrl in controls:
            tp.Dcc.connect_message_attribute(self._switch_parent, ctrl, '{}Parent'.format(self._switch_attribute_name))

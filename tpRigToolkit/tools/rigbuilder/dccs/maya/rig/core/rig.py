#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base rig implementation for tpRigToolkits-tools-rigbuilder-dccs-maya
"""

from __future__ import print_function, division, absolute_import

import string

import tpDcc as tp
from tpDcc.libs.python import osplatform, python

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import control


class Rig(object):
    """
    Base class to create rigs
    """

    SIDE_LEFT = 'L'
    SIDE_RIGHT = 'R'
    SIDE_CENTER = 'C'

    def __init__(self, description, side=None):

        tp.Dcc.refresh_viewport()

        self._side = side
        self._description = description
        self._joints = list()
        self._buffer_joints = list()
        self._control_inst = None
        self._set_sub_control_color_only = False
        self._control_group = None
        self._setup_group = None
        self._control_parent = None
        self._setup_parent = None
        self._delete_setup = False
        self._control_shape = 'circle'
        self._sub_control_shape = None
        self._control_color = None                          # Defines the color of the controls
        self._sub_control_color = None                      # Defines the color of the sub controls
        self._control_size = 1                              # Defines the default size of the control curve
        self._sub_control_size = 0.8                        # Defines the default size of the sub control curve
        self._control_offset_axis = None
        self._controls = list()
        self._sub_controls = list()
        self._sub_controls_with_buffer = list()
        self._control_dict = dict()
        self._sub_visibility = False
        self._connect_sub_vis_attr = None
        self._connect_important = True
        self._connect_important_node = None
        self._control_number = True
        self._custom_sets = list()
        self._switch_parent = None
        self._pick_walk_parent = None

        self._handle_side_variations()
        self._create_default_groups()

    def __getattribute__(self, item):
        custom_functions = ['create']
        if item in custom_functions:
            results = object.__getattribute__(self, item)
            result_values = results()

            def results():
                return result_values

            if item == 'create':
                self._post_create()

            return results
        else:
            return object.__getattribute__(self, item)

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def side(self):
        return self._side

    @property
    def description(self):
        return self._description

    @property
    def controls(self):
        return self._controls

    @property
    def sub_controls(self):
        return self._sub_controls

    @property
    def sub_controls_with_buffer(self):
        return self._sub_controls_with_buffer

    @property
    def joints(self):
        return self._joints

    @property
    def ik_handle(self):
        return self._ik_handle

    @property
    def control_group(self):
        return self._control_group

    @property
    def setup_group(self):
        return self._setup_group

    @property
    def set_sub_control_color_only(self):
        return self._set_sub_control_color_only

    @set_sub_control_color_only.setter
    def set_sub_control_color_only(self, flag):
        self._set_sub_control_color_only = flag

    @property
    def control_offset_axis(self):
        return self._control_offset_axis

    @control_offset_axis.setter
    def control_offset_axis(self, axis_letter):
        self._control_offset_axis = axis_letter.lower()

    @property
    def switch_parent(self):
        return self._switch_parent

    @switch_parent.setter
    def switch_parent(self, value):
        self._switch_parent = value

    @property
    def connect_important(self):
        return self._connect_important

    @connect_important.setter
    def connect_important(self, flag):
        self._connect_important = flag

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def create(self):
        """
        Creates teh rig. Rig attributes must be set before running this function
        """

        tpRigToolkit.logger.info(
            'Creating rig: {}, description: {}, side: {}'.format(
                self.__class__.__name__, self._description, self._side))
        tpRigToolkit.logger.info('\nUsing joints: {}'.format(self._joints))
        self._parent_default_groups()
        if self._delete_setup:
            self.delete_setup()

    def get_control_size(self):
        """
        Returns the size of the controls
        """

        return self._control_size

    def set_control_size(self, value):
        """
        Sets the size of the control
        :param value: float
        """

        if value == 0:
            tpRigToolkit.logger.warning('Setting control size to zero!')
        self._control_size = value

    def get_control_color(self):
        """
        Returns control color
        :return: list(float, float, float) or int
        """

        return self._control_color

    def set_control_color(self, value):
        """
        Sets control color
        :param value: list(float, float, float) or int
        """

        self._control_color = value

    def set_control_parent(self, parent_transform):
        """
        Sets the parent of the control groups for this rig
        This function is usually called after calling create function
        :param parent_transform: str
        """

        self._control_parent = parent_transform
        self._parent_default_group(self._control_group, self._control_parent)

    def set_setup_parent(self, parent_transform):
        """
        Sets the parent of the setup group for this rig
        This function is usually called after calling create function
        :param parent_transform: str
        """

        self._setup_parent = parent_transform
        self._parent_default_group(self._setup_group, self._setup_parent)

    def set_switch_parent(self, rig_control_group):
        """
        Sets switch parent of the rig
        :param rig_control_group: str
        """

        self._switch_parent = rig_control_group

    def get_control_shape(self):
        """
        Returns the shape of the controls of the rig
        :return: str
        """

        return self._control_shape

    def set_control_shape(self, value):
        """
        Sets the look of the curve for the controls
        :param value: str
        """

        self._control_shape = value

    def get_sub_control_size(self):
        """
        Returns the size of the sub controls of the rig
        :return: float
        """

        return self._sub_control_size

    def set_sub_control_size(self, value):
        """
        Sets the size of the sub controls of the rig
        :return: float
        """

        self._sub_control_size = value

    def get_sub_control_color(self):
        """
        Returns the color of the sub controls of the rig
        :return: list(int, int, int) or int
        """

        return self._sub_control_color

    def set_sub_control_color(self, value):
        """
        Sets sub controls color
        :param value: list(float, float, float) or int
        """

        self._sub_control_color = value

    def get_sub_control_shape(self):
        """
        Returns the shape of the sub controls of the rig
        :return: str
        """

        return self._sub_control_shape

    def set_sub_control_shape(self, value):
        """
        Sets the look of the curve for the sub controls
        :param value: str
        """

        self._sub_control_shape = value

    def get_sub_visibility(self):
        """
        Returns whether or not sub controls are visible by default
        :return: bool
        """

        return self._sub_visibility

    def set_sub_visibility(self, flag):
        """
        Sets whether or not sub controls are visible by default
        :param flag: bool
        """

        self._sub_visibility = flag

    def delete_setup(self):
        """
        Function that cleans nodes used to setup rig
        """

        if tp.Dcc.object_exists(self._setup_group):
            if tp.Dcc.node_is_empty(self._setup_group):
                parent = tp.Dcc.node_parent(self._setup_group)
                if parent:
                    tpRigToolkit.logger.warning('Setup group is parented. Skipping deletion!')
                else:
                    tp.Dcc.delete_object(self._setup_group)
                    return
            else:
                if self._delete_setup:
                    tpRigToolkit.logger.warning('Setup group is not empty. Skipping deletion!')
        else:
            if self._delete_setup:
                tpRigToolkit.logger.warning('Setup group does not exists. Skipping deletion!')

        if self._delete_setup:
            tpRigToolkit.logger.warning(
                'Could not delete setup group. rig: {} side: {} of class: {}'.format(
                    self._description, self._side, self.__class__.__name__))

        self._delete_setup = True

    # ==============================================================================================
    # GROUPS
    # ==============================================================================================

    def _create_default_groups(self):
        """
        Internal function that creates default groups for rig
        """

        self._control_group = self._create_control_group()
        self._setup_group = self._create_setup_group()
        self._create_control_group_attributes()
        tp.Dcc.hide_node(self._setup_group)
        self._parent_default_groups()

    def _create_group(self, prefix=None, description=None):
        """
        Internal function that creates a new empty group
        :param prefix: str
        :param description: str
        :return: str
        """

        rig_group_name = self._get_name(prefix, description)
        unique_name = tp.Dcc.find_unique_name(rig_group_name)
        group = tp.Dcc.create_empty_group(name=unique_name)

        return group

    def _parent_default_group(self, group, parent):
        """
        Internal function that is used to parent a default group to a specific parent
        :param group: str
        :param parent: str
        """

        if not group or not parent:
            return

        if not tp.Dcc.object_exists(group):
            return
        if not tp.Dcc.object_exists(parent):
            tpRigToolkit.logger.warning('{} does not exists to be a parent!'.format(parent))
            return

        parent_node = tp.Dcc.node_parent(group, full_path=False) or ''
        parent_node_full = tp.Dcc.node_parent(group, full_path=True) or ''
        if parent == parent_node or parent == parent_node_full:
            return

        try:
            tp.Dcc.set_parent(group, parent)
        except Exception as exc:
            tpRigToolkit.logger.warning('Was not possible to parent {} | {} - {}'.format(group, parent, exc))

    def _parent_default_groups(self):
        """
        Internal function that parent default groups
        """

        self._parent_default_group(self._control_group, self._control_parent)
        self._parent_default_group(self._setup_group, self._setup_parent)

    def _create_control_group(self, description=''):
        """
        Internal function that creates default control group for rig
        :param description: str
        :return: str
        """

        group = self._create_group('controls', description)
        if self._control_group:
            tp.Dcc.set_parent(group, self._setup_group)

        return group

    def _create_setup_group(self, description=''):
        """
        Internal function that creates default setup group for rig
        :param description: str
        :return: str
        """

        group = self._create_group('setup', description)
        if self._setup_group:
            tp.Dcc.set_parent(group, self._setup_group)

        return group

    def _create_control_group_attributes(self):
        """
        Internal function that creates default attributes for rig control group
        """

        tp.Dcc.add_bool_attribute(self._control_group, 'rigControlGroup', default_value=True)
        tp.Dcc.lock_attribute(self._control_group, 'rigControlGroup')

        tp.Dcc.add_string_attribute(self._control_group, 'description')
        tp.Dcc.set_string_attribute_value(self._control_group, 'description', self._description)
        tp.Dcc.lock_attribute(self._control_group, 'description')

        tp.Dcc.add_string_attribute(self._control_group, 'side')
        side = self._side or ''
        tp.Dcc.set_string_attribute_value(self._control_group, 'side', side)

    # ==============================================================================================
    # SIDE
    # ==============================================================================================

    def _handle_side_variations(self):
        """
        Internal callback that sets rig side depending on the side nomenclature
        """

        if tp.Dcc.name_is_left(self._side):
            self._side = 'L'
        elif tp.Dcc.name_is_right(self._side):
            self._side = 'R'
        elif tp.Dcc.name_is_center(self._side):
            self._side = 'C'
        else:
            raise Exception('Side "{}" is not supported!'.format(self._side))

        # ==============================================================================================
        # CONTROLS
        # ==============================================================================================

    def get_controls(self, title):
        """
        Returns controls with title in its entry name
        :param title: str
        :return:
        """

        found = list()
        for ctrl in self._controls:
            if title in self._control_dict[ctrl]:
                found.append(self._control_dict[ctrl][title])

        return found

    def get_sub_controls(self, title):
        """
        Returns sub controls with title in its entry name
        :param title: str
        :return:
        """

        found = list()
        for ctrl in self._sub_controls:
            if title in self._control_dict[ctrl]:
                found.append(self._control_dict[ctrl][title])

        return found

    def get_all_controls(self):
        """
        Returns all controls in current rig
        :return:
        """

        return self._control_dict.keys()

    def _get_control_name(self, description=None, sub=False):
        """
        Internal function that returns a proper control name for the current rig
        :param description: str
        :param sub: bool
        :return: str
        """

        current_rig = osplatform.get_env_var('RIGBUILDER_CURRENT_SCRIPT')
        if current_rig:
            control_inst = control.ControlNameFromFile(current_rig)
            if sub is False:
                control_inst.control_number = self._control_number
            self._control_inst = control_inst
            if description:
                description = '{}_{}'.format(self._description, description)
            else:
                description = self._description

            if sub is True:
                description = 'sub_{}'.format(description)
            control_name = control_inst.get_name(description, self._side)
        else:
            prefix = 'CNT'
            if sub:
                prefix = 'CNT_SUB'
            control_name = self._get_name(prefix, description, sub=sub)
            control_name = control_name.upper()

        control_name = tp.Dcc.find_unique_name(control_name)

        return control_name

    def _create_control(self, description=None, sub=False, curve_type=None):
        """
        Internal function that creates a new control for current rig
        :param description: str
        :param sub: bool
        :param curve_type: str
        :return: str
        """

        new_ctrl = control.Control(self._get_control_name(description, sub))
        if curve_type:
            new_ctrl.set_curve_type(curve_type)

        side = self._side or 'C'

        if not self._set_sub_control_color_only:
            new_ctrl.color(tp.Dcc.get_color_of_side(side, sub))
        if self._set_sub_control_color_only:
            new_ctrl.color(tp.Dcc.get_color_of_side(side, True))

        if self._control_color >= 0:
            if sub:
                new_ctrl.color(self._sub_control_color)
            else:
                new_ctrl.color(self._control_color)

        new_ctrl.hide_visibility_attribute()

        if self._control_shape and not curve_type:
            new_ctrl.set_curve_type(self._control_shape)
            if sub:
                if self._sub_control_shape:
                    new_ctrl.set_curve_type(self._sub_control_shape)

        if sub:
            size = self._control_size * self._sub_control_size
            self._sub_controls.append(new_ctrl.get())
            self._sub_controls_with_buffer[-1] = new_ctrl.get()
        else:
            size = self._control_size
            self._controls.append(new_ctrl.get())
            self._sub_controls_with_buffer.append(None)
        new_ctrl.scale_shape(size, size, size)

        if self._control_offset_axis:
            if self._control_offset_axis == 'x':
                new_ctrl.rotate_shape(90, 0, 0)
            elif self._control_offset_axis == 'y':
                new_ctrl.rotate_shape(0, 90, 0)
            elif self._control_offset_axis == 'z':
                new_ctrl.rotate_shape(0, 0, 90)
            elif self._control_offset_axis == '-x':
                new_ctrl.rotate_shape(-90, 0, 0)
            elif self._control_offset_axis == '-y':
                new_ctrl.rotate_shape(0, -90, 0)
            elif self._control_offset_axis == '-z':
                new_ctrl.rotate_shape(0, 0, -90)

        self._control_dict[new_ctrl.get()] = dict()

        return new_ctrl

    # ==============================================================================================
    # PRIVATE
    # ==============================================================================================

    def _get_name(self, prefix=None, description=None, sub=False):
        """
        Internal function that returns name for rig nodes
        :param prefix: str
        :param description: str
        :param sub: bool
        :return: str
        """

        if self._side:
            name_list = [prefix, self._description, description, '1', self._side]
        else:
            name_list = [prefix, self._description, description, '1', self._side]

        filtered_name_list = list()

        for name in name_list:
            if name:
                filtered_name_list.append(str(name))

        name = string.join(filtered_name_list, '_')

        return name

    def _connect_sub_visibility(self, control_and_attr, sub_control):
        shapes = tp.Dcc.list_shapes(sub_control)
        control_name = tp.Dcc.node_short_name(control_and_attr, remove_attribute=True)
        control_attr = tp.Dcc.node_attribute_name(control_and_attr)
        for shape in shapes:
            tp.Dcc.connect_visibility(control_name, control_attr, shape, self._sub_visibility)
            if self._connect_sub_vis_attr:
                node = tp.Dcc.node_short_name(self._connect_sub_vis_attr)
                attr = tp.Dcc.node_attribute_name(self._connect_sub_vis_attr)
                if not tp.Dcc.attribute_exists(node, attr):
                    tp.Dcc.add_bool_attribute(node, attr, default_value=self._sub_visibility, keyable=True)
                if not tp.Dcc.is_attribute_connected(control_name, control_attr):
                    tp.Dcc.connect_attribute(node, attr, control_name, control_attr)

    def _post_create(self):
        tp.Dcc.add_string_attribute(self._control_group, 'className')
        tp.Dcc.set_string_attribute_value(self._control_group, 'className', str(self.__class__.__name__))

        if tp.Dcc.object_exists(self._setup_group):
            if tp.Dcc.node_is_empty(self._setup_group):
                parent = tp.Dcc.node_parent(self._setup_group)
                if not parent:
                    class_name = self.__class__.__name__
                    tpRigToolkit.logger.warning('Empty setup group in class: {} with description {} and side {}'.format(
                        class_name, self._description, self._side))

        try:
            self._post_create_rotate_order()
        except Exception as exc:
            tpRigToolkit.logger.warning('Was not possible toe add rotate order to channel box: {}'.format(exc))

        if self._connect_important:
            self._post_create_connect('controls', 'control')
            self._post_create_connect('sub_controls_with_buffer', 'subControl')
            self._post_create_connect('joints', 'joint')
            self._post_create_connect('ik_handle', 'ikHandle')
            if self._joints:
                tp.Dcc.connect_message_attribute(self._control_group, self._joints[0], 'rig1')

        self._post_add_shape_switch()

        self._post_store_orig_matrix('controls')
        self._post_store_orig_matrix('sub_controls_with_buffer')
        self._post_store_orig_matrix('joints')

        self._post_add_to_control_set()
        self._post_connect_controller()
        self._post_connect_controls_to_switch_parent()

    def _post_create_rotate_order(self):
        for ctrl in self._controls:
            count = 0
            for axis in 'XYZ':
                if not tp.Dcc.is_attribute_locked(ctrl, 'rotate{}'.format(axis)):
                    count += 1
            if count == 3:
                tp.Dcc.show_attribute(ctrl, 'rotateOrder')

    def _post_create_connect(self, inst_attribute, description):
        if hasattr(self, inst_attribute):
            value = getattr(self, inst_attribute)
            if value:
                i = 1
                value = python.force_list(value)
                for sub_value in value:
                    tp.Dcc.connect_message_attribute(sub_value, self._control_group, '{}{}'.format(description, i))
                    i += 1

                return value

    def _post_add_shape_switch(self):
        if hasattr(self, 'create_buffer_joints'):
            if not self.create_buffer_joints:
                return
        else:
            return

        if not hasattr(self, 'switch_shape_attribute_name'):
            return

        if not self._switch_shape_attribute_name:
            return

        shapes = tp.Dcc.list_shapes_of_type(self._joints[0], shape_type='locator', intermediate_shapes=False)
        name = self._switch_shape_attribute_name
        if self._switch_shape_node_name:
            node_name = self._switch_shape_node_name
        else:
            if self._switch_shape_attribute_name:
                node_name = self._switch_shape_attribute_name

        if tp.Dcc.object_exists(node_name) and tp.Dcc.node_is_a_shape(node_name):
            shapes = [node_name]

        if not shapes:
            locator = tp.Dcc.create_locator()
            shapes = tp.Dcc.list_shapes_of_type(self._joints[0], shape_type='locator', intermediate_shapes=False)
            for axis in 'XYZ':
                tp.Dcc.set_numeric_attribute_value(shapes[0], 'localScale'.format(axis), 0)
            tp.Dcc.hide_attributes(shapes[0], ['localPosition', 'localScale'])
            shapes = tp.Dcc.set_shape_parent(shapes[0], self._joints[0])
            tp.Dcc.delete_object(locator)
            shapes[0] = tp.Dcc.rename_node(shapes[0], tp.Dcc.find_unique_name(node_name))

        joint_shape = shapes[0]

        if not tp.Dcc.attribute_exists(joint_shape, name):
            tp.Dcc.add_float_attribute(joint_shape, name, keyable=True, min_value=0)
        if not tp.Dcc.is_attribute_connected(self._joints[0], 'switch'):
            tp.Dcc.connect_attribute(joint_shape, name, self._joints[0], 'switch')

        max_value = tp.Dcc.get_maximum_float_attribute_value(node=self._joints[0], attribute_name='switch')
        try:
            test_max = tp.Dcc.get_maximum_float_attribute_value(node=joint_shape[0], attribute_name=name)
            if max_value < test_max:
                max_value = test_max
        except Exception:
            pass

        tp.Dcc.set_maximum_float_attribute_value(joint_shape, name, max_value=max_value)
        tp.Dcc.set_numeric_attribute_value(joint_shape, name, attribute_value=max_value)
        for ctrl in self._controls:
            tp.Dcc.add_node_to_parent(shapes[0], ctrl)
        tp.Dcc.connect_message_attribute(shapes[0], self._control_group, 'switch')

    def _post_store_orig_matrix(self, inst_attribute):
        if hasattr(self, inst_attribute):
            value = getattr(self, inst_attribute)
            if value:
                value = python.force_list(value)
                for sub_value in value:
                    if sub_value:
                        tp.Dcc.store_world_matrix_to_attribute(
                            sub_value, attribute_name='origMatrix', skip_if_exists=True)

                return value

    def _post_add_to_control_set(self):
        set_name = 'set_controls'
        exists = False
        if tp.Dcc.object_exists(set_name) and tp.Dcc.node_is_selection_group(set_name):
            exists = True
        if not exists:
            sets = tp.Dcc.get_selection_groups('*{}'.format(set_name))
            if sets:
                set_name = sets[0]
                exists = True
            if not exists:
                tp.Dcc.create_selection_group(name=tp.Dcc.find_unique_name(set_name), empty=True)

        parent_set = set_name
        child_set = None
        for set_name in self._custom_sets:
            if set_name == parent_set:
                continue
            custom_set_name = 'set_{}'.format(set_name)
            if not tp.Dcc.object_exists(custom_set_name):
                custom_set_name = tp.Dcc.create_selection_group(name=custom_set_name, empty=True)
            tp.Dcc.add_node_to_selection_group(custom_set_name, parent_set)
            parent_set = custom_set_name

        if self.__class__ != Rig:
            child_set = 'set_{}'.format(self._description)
            if self._side:
                child_set = 'set_{}_{}'.format(self._description, self._side)
            if child_set != parent_set:
                if not tp.Dcc.object_exists(child_set):
                    tp.Dcc.create_selection_group(name=child_set, empty=True)
                tp.Dcc.add_node_to_selection_group(child_set, parent_set)

        if not child_set:
            child_set = parent_set

        controls = self.get_all_controls()
        for ctrl in controls:
            tpRigToolkit.logger.info('Adding {} to control sets'.format(ctrl))
            tp.Dcc.add_node_to_selection_group(ctrl, child_set)

    def _post_connect_controller(self):
        if tp.is_maya():
            import tpDcc.dccs.maya as maya

        controller = tp.Dcc.get_message_input(self._control_group, 'control1')
        parent = tp.Dcc.node_parent(self._control_group)
        if parent:
            parent = parent[0]

        if tp.is_maya():
            if controller and parent:
                if maya.cmds.controller(controller, q=True, isController=True) and maya.cmds.controller(
                        parent, q=True, isController=True):
                    maya.cmds.controller(controller, parent, p=True)

    def _post_connect_controls_to_switch_parent(self):
        if not self._switch_parent:
            return

        controls = self.get_all_controls()
        for ctrl in controls:
            tp.Dcc.connect_message_attribute(self._switch_parent, ctrl, 'switchParent')

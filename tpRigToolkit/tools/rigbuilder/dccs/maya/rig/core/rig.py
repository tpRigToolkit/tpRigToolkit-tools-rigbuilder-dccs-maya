#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base rig implementation for tpRigToolkits-tools-rigbuilder-dccs-maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.libs.python import python

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.core import control


class Rig(object):
    """
    Base class to create rigs
    """

    def __init__(self, *args, **kwargs):
        super(Rig, self).__init__()

        tp.Dcc.refresh_viewport()

        self._side = kwargs.get('side', api.get_default_side())     # Side of the rig component
        self._description = kwargs.get('description', 'rig')        # Description of the rig component

        self._controls = list()                                     # List of all controls of the rig component
        self._sub_controls = list()                                 # List of all sub controls of the rig component
        self._controls_dict = dict()                                # Dict that maps controls with sub controls
        self._sub_controls_with_buffer = list()                     # Lif of sub controls with buffer group
        self._connect_sub_vis_attr = None                           # Node that contains sub visibility attribute

        self._control_size = 1.0                                    # Size of the controls of the rig component
        self._control_shape = None                                  # Shape used by the controls of the rig component
        self._control_color = None                                  # Color of the controls of the rig component
        self._control_parent = None                                 # Parent group for the rig component controls group
        self._sub_control_size = 0.8                                # Size of the sub controls of the rig component
        self._sub_control_shape = None                              # Shape used by sub controls of the rig component
        self._sub_control_color = None                              # Color used by sub controls of the rig component
        self._set_sub_control_color_only = False                    # Sets whether side colors will use standard or sub
        self._create_sub_controls = False                           # Sets if sub controls will be created or not
        self._control_descriptions = dict()                         # Stores the description of each one of the controls
        self._control_data = dict()                                 # Stores the data of each of the controls
        self._custom_sets = list()                                  # List of custom sets used by rig component
        self._pick_walk_parent = None                               # Parent used to pick walk using Maya controller
        self._use_side_colors = False                               # Sets if side colors should be used for controls
        self._control_offset_axis = None                            # Rotation offset axis for the controls
        self._mirror = False                                        # Sets whether or not current rig is a mirror
        self._sub_visibility = False                                # Sets whether sub controls should be vis by default

        self._setup_parent = None                                   # Parent group for the rig component setup group
        self._delete_setup = False                                  # Sets if extra nodes should be deleted after build
        self._controls_group = None                                 # Group that contains all rig controls
        self._setup_group = None                                    # Group that contains all setup rig nodes

        self._connect_messages = True                               # Sets if rig should use messages to connect info
        self._connect_messages_node = None                          # Node that rig component messages are connected to

        self._create_default_groups()

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
    def mirror(self):
        return self._mirror

    @property
    def controls_group(self):
        return self._controls_group

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def __getattribute__(self, item):
        def results():
            return result_values

        custom_functions = ['create']
        if item in custom_functions:
            result = object.__getattribute__(self, item)
            result_values = result()
            if item == 'create':
                self._post_create()

            return results
        else:
            return object.__getattribute__(self, item)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def create(self):
        """
        Creates the rig. Rig attributes must be set before running this function
        """

        tpRigToolkit.logger.info(
            'Creating rig: {}, description: {}, side: {}'.format(
                self.__class__.__name__, self._description, self._side))
        self._parent_default_groups()
        if self._delete_setup:
            self.delete_setup()

    def set_mirror(self, flag):
        """
        Sets whether this rig component is a mirror one or not
        :param flag: bool
        """

        self._mirror = flag

    def set_connect_messages(self, flag):
        """
        Sets whether or not custom messages of the rig will be connected
        :param flag: bool
        """

        self._connect_messages = flag

    def set_setup_parent(self, parent_transform):
        """
        Sets the parent of the setup group for this rig
        This function is usually called after calling create function
        :param parent_transform: str
        """

        self._setup_parent = parent_transform
        self._parent_default_group(self._setup_group, self._setup_parent)

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
    # CONTROLS
    # ==============================================================================================

    def get_all_controls(self):
        """
        Returns all controls of the current rig
        :return: list(str)
        """

        return self._controls_dict.keys()

    def get_control_groups(self, group_type):
        """
        Returns control groups that match given type
        :param group_type: str, 'buffer' or 'driver'
        :return: list(str)
        """

        entries = list()
        for ctrl in self._controls:
            if group_type in self._controls_dict[ctrl]:
                entries.append(self._controls_dict[ctrl][group_type])

        return entries

    def get_sub_control_groups(self, group_type):
        """
        Returns sub control groups that match given type
        :param group_type: str, 'buffer' or 'driver'
        :return: list(str)
        """

        entries = list()
        for ctrl in self._sub_controls:
            if group_type in self._controls_dict[ctrl]:
                entries.append(self._controls_dict[ctrl][group_type])

        return entries

    def get_control_size(self):
        """
        Returns the size of the controls of this rig component
        :return: float
        """

        return self._control_size

    def set_control_size(self, value):
        """
        Sets the size of the controls
        :param value:
        :return:
        """

        if value == 0.0:
            value = 0.1

        self._control_size = value

    def get_sub_control_size(self):
        """
        Returns the size of the sub controls
        :return: float
        """

        return self._sub_control_size

    def set_sub_control_size(self, value):
        """
        Sets the size of the sub controls
        :param value:
        :return:
        """

        if value == 0.0:
            value = 0.1

        self._sub_control_size = value

    def get_control_shape(self):
        """
        Returns control shape
        :return: str
        """

        return self._control_shape

    def set_control_shape(self, shape_name):
        """
        Sets shape of the controls
        :param shape_name: str
        """

        self._control_shape = shape_name

    def get_sub_control_shape(self):
        """
        Returns sub control shape
        :return: str
        """

        return self._sub_control_shape

    def set_sub_control_shape(self, shape_name):
        """
        Sets shape of the sub controls
        :param shape_name: str
        """

        self._sub_control_shape = shape_name

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

    def get_sub_control_color(self):
        """
        Returns sub control color
        :return: list(float, float, float) or int
        """

        return self._sub_control_color

    def set_sub_control_color(self, value):
        """
        Sets sub control color
        :param value: list(float, float, float) or int
        """

        self._sub_control_color = value

    def set_control_parent(self, parent_transform):
        """
        Sets the parent of the control groups for this rig
        This function is usually called after calling create function
        :param parent_transform: str
        """

        self._control_parent = parent_transform
        self._parent_default_group(self._controls_group, self._control_parent)

    def set_control_offset_axis(self, axis_letter):
        """
        Sets the axis that control curve CVs will rotate offset to.
        Control will be rotated 90 degrees (or -90 degrees is axis is negative) in the given axis.
        :param axis_letter: str, (x, -x, y, -y, z, -z)
        """

        self._control_offset_axis = axis_letter.lower()

    def set_pick_walk_parent(self, control_name):
        """
        Sets the parent control for pick walk functionality
        :param control_name: str
        """

        self._pick_walk_parent = control_name

    def set_control_description(self, description, index=0):
        """
        Sets the description of the control at the given index
        :param description: str
        :param index: int
        """

        self._control_descriptions[index] = description

    def set_control_data(self, data_dict, index=0):
        """
        Sets the data of the control at the given index
        :param data_dict: dict
        :param index: int
        """

        self._control_data[index] = data_dict

    def set_sub_control_color_only(self, flag):
        """
        Sets whether or not sub control colors are used for all controls
        :param flag: bool
        """

        self._set_sub_control_color_only = flag

    def set_use_side_colors(self, flag):
        """
        Sets whether or not controls should use side colors
        :param flag: bool
        :return:
        """

        self._use_side_colors = flag

    def set_sub_visibility(self, flag):
        """
        Sets whether sub controls are visibly by default or not
        :param flag: bool
        """

        self._sub_visibility = flag

    def set_connect_sub_visibility_attribute_name(self, attribute_name):
        """
        Sets the name of the attribute that subVisibility attribute will be connected to
        :param attribute_name: str
        """

        self._connect_sub_vis_attr = attribute_name

    def set_control_sets(self, list_of_set_names):
        """
        Sets the list of sets where all controls generated under the last set name in the list
        :param list_of_set_names: list(str)
        """

        self._custom_sets = python.force_list(list_of_set_names)

    # ==============================================================================================
    # GROUPS
    # ==============================================================================================

    def _create_default_groups(self):
        """
        Internal function that creates default groups for current rig
        """

        self._controls_group = self._create_controls_group()
        self._setup_group = self._create_setup_group()
        self._create_controls_group_attributes()
        tp.Dcc.hide_node(self._setup_group)
        self._parent_default_groups()

    def _create_controls_group_attributes(self):
        """
          Internal function that creates default attributes for rig control group
          """

        tp.Dcc.add_bool_attribute(self._controls_group, 'rigControlGroup', default_value=True)
        tp.Dcc.lock_attribute(self._controls_group, 'rigControlGroup')
        tp.Dcc.add_string_attribute(self._controls_group, 'description')
        tp.Dcc.set_string_attribute_value(self._controls_group, 'description', self._description)
        tp.Dcc.lock_attribute(self._controls_group, 'description')
        tp.Dcc.add_string_attribute(self._controls_group, 'side')
        side = self._side or 'c'
        tp.Dcc.set_string_attribute_value(self._controls_group, 'side', side)

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

        self._parent_default_group(self._controls_group, self._control_parent)
        self._parent_default_group(self._setup_group, self._setup_parent)

    def _create_group(self, *args, **kwargs):
        """
        Internal function that creates a new empty group for this rig
        :param prefix: str
        :param description: str
        :return: str
        """

        rig_group_name = self._get_name(*args, **kwargs)
        unique_name = tp.Dcc.find_unique_name(rig_group_name)
        group = tp.Dcc.create_empty_group(name=unique_name)

        return group

    def _create_controls_group(self, description=''):
        """
        Internal function that creates group for rig controls
        :return: str
        """

        control_group = self._create_group('controls', description or self._description)
        if self._controls_group:
            tp.Dcc.set_parent(control_group, self._setup_group)

        return control_group

    def _create_setup_group(self, description=''):
        """
        Internal function that creates group for rig setups
        :return: str
        """

        setup_group = self._create_group('setup', description or self._description)
        if self._setup_group:
            tp.Dcc.set_parent(setup_group, self._setup_group)

        return setup_group

    # ==============================================================================================
    # CONTROLS
    # ==============================================================================================

    def _create_control(self, *args, **kwargs):
        """
        Internal function that creates a new control for current rig
        :param args:
        :param kwargs:
        :return: RigControl
        """

        curve_type = kwargs.pop('curve_type', None)
        sub = kwargs.pop('sub', False)
        control_data = kwargs.pop('control_data', dict())

        new_ctrl = control.RigControl(self._get_control_name(*args, **kwargs))
        tp.Dcc.set_parent(new_ctrl.control(), self._controls_group)

        if control_data:
            if 'offset' in control_data and self._mirror:
                control_data['offset'][0] *= -1
            new_ctrl.set_data(control_data)

        if curve_type:
            new_ctrl.set_curve_type(curve_type)

        if self._use_side_colors:
            if self._set_sub_control_color_only:
                new_ctrl.set_color(api.get_color_of_side(self._side, sub_color=True))
            else:
                new_ctrl.set_color(api.get_color_of_side(self._side, sub_color=False))

        if self._control_color is not None and not sub:
            new_ctrl.set_color(self._control_color)
        if self._sub_control_color is not None and sub:
            new_ctrl.set_color(self._sub_control_color)

        if self._control_shape and not curve_type:
            new_ctrl.set_curve_type(self._control_shape)
            if sub and self._sub_control_shape:
                new_ctrl.set_curve_type(self._sub_control_shape)

        if sub:
            size = self._control_size * self._sub_control_size
        else:
            size = self._control_size
        new_ctrl.scale_shape(size, size, size)

        new_ctrl.hide_visibility_attribute()

        if sub:
            self._sub_controls.append(new_ctrl.get())
            self._sub_controls_with_buffer[-1] = new_ctrl.get()
        else:
            self._controls.append(new_ctrl.get())
            self._sub_controls_with_buffer.append(None)

        if self._control_offset_axis:
            offset_rotation = None
            if self._control_offset_axis[-1] == 'x':
                offset_rotation = [-90, 0, 0] if self._control_offset_axis[0] == '-' else [90, 0, 0]
            elif self._control_offset_axis[-1] == 'y':
                offset_rotation = [0, -90, 0] if self._control_offset_axis[0] == '-' else [0, 90, 0]
            elif self._control_offset_axis[-1] == 'z':
                offset_rotation = [0, 0, -90] if self._control_offset_axis[0] == '-' else [0, 0, 90]
            if offset_rotation:
                new_ctrl.rotate_shape(*offset_rotation)

        self._controls_dict[new_ctrl.get()] = dict()

        return new_ctrl

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _get_name(self, *args, **kwargs):
        """
        Internal function that returns names for rig nodes
        :param prefix: str
        :param description: str
        :return: str
        """

        current_project = api.get_current_project()
        if current_project:
            rule = current_project.get_name_rule()
            if rule:
                rule_name = rule.name
                kwargs['rule_name'] = rule_name

        kwargs['description'] = self._description
        kwargs['side'] = self._side

        return api.solve_name(*args, **kwargs)

    def _get_control_name(self, *args, **kwargs):
        """
        Internal function that returns a proper control name for the current rig
        :param args:
        :param kwargs:
        :return: str
        """

        current_project = api.get_current_project()
        if current_project:
            controls_name_rule = current_project.options.get('controls_name_rule', None)
            kwargs['rule_name'] = controls_name_rule

        kwargs['description'] = self._description
        kwargs['side'] = self._side

        return api.solve_name(*args, **kwargs)

    def _connect_sub_visibility(self, control_and_attr, sub_control):
        """

        :param control_and_attr:
        :param sub_control:
        :return:
        """

        shapes = tp.Dcc.list_shapes(sub_control) or list()
        for shape in shapes:
            control_node = tp.Dcc.node_short_name(control_and_attr, remove_attribute=True)
            control_attr = tp.Dcc.node_attribute_name(control_and_attr)
            tp.Dcc.connect_visibility(control_node, control_attr, shape, self._sub_visibility)

            if self._connect_sub_vis_attr:
                control_node = tp.Dcc.node_short_name(control_and_attr, remove_attribute=True)
                control_attr = tp.Dcc.node_attribute_name(control_and_attr)
                sub_node = tp.Dcc.node_short_name(self._connect_sub_vis_attr, remove_attribute=True)
                sub_attr = tp.Dcc.node_attribute_name(self._connect_sub_vis_attr)

                if not tp.Dcc.object_exists(self._connect_sub_vis_attr):
                    tp.Dcc.add_bool_attribute(sub_node, sub_attr, self._sub_visibility, keyable=True)

                if not tp.Dcc.is_attribute_connected(control_node, control_attr):
                    tp.Dcc.connect_attribute(sub_node, sub_attr, control_node, control_attr)

    def _post_create(self):
        """
        Internal function that is created after the rig is created
        """

        tp.Dcc.add_string_attribute(self._controls_group, 'className', str(self.__class__.__name__))
        if tp.Dcc.object_exists(self._setup_group):
            if tp.Dcc.node_is_empty(self._setup_group):
                parent = tp.Dcc.node_parent(self._setup_group)
                if not parent:
                    tpRigToolkit.logger.warning(
                        'Empty setup group in class: {} with description: {} and side: {}'.format(
                            self.__class__.__name__, self._description, self._side))

        try:
            self._post_create_rotate_order()
        except Exception as exc:
            tpRigToolkit.logger.warning('Impossible to add rotate order to channel box: {}'.format(exc))

        if self._connect_messages:
            self._post_create_messages()

        self._post_store_orig_matrix('controls')
        self._post_store_orig_matrix('_sub_controls_with_buffer')

        self._post_add_to_control_set()
        self._post_connect_controller()

    def _post_create_messages(self):
        """
        Internal function that is called during post create function
        Creates custom messages to rig controls group
        """

        self._post_create_message('_controls', 'control')
        self._post_create_message('_sub_controls_with_buffer', 'subControl')

    def _post_create_rotate_order(self):
        """
        Internal function that is called during post create function
        Makes sure that rotate order axis is available in channel box for all rig controls
        """

        for ctrl in self._controls:
            is_locked = False
            for axis in 'XYZ':
                if tp.Dcc.is_attribute_locked(ctrl, 'rotate{}'.format(axis)):
                    is_locked = True
            if is_locked:
                continue

            tp.Dcc.show_attribute(ctrl, 'rotateOrder')
            tp.Dcc.keyable_attribute(ctrl, 'rotateOrder')

    def _post_create_message(self, attr_name, description):
        """
        Internal function that connects attribute to rig controls group through a message
        :param description: str
        :return:
        """

        if not hasattr(self, attr_name):
            return

        value = getattr(self, attr_name)
        if value is None:
            return

        index = 1
        value = python.force_list(value)
        for sub_value in value:
            tp.Dcc.connect_message_attribute(sub_value, self._controls_group, '{}{}'.format(description, index))
            index += 1

        return value

    def _post_store_orig_matrix(self, attr_name):
        """
        Internal function that stores original world matrix of a specific node in an attribute
        :param attr_name: str
        :return:
        """

        if not hasattr(self, attr_name):
            return

        value = getattr(self, attr_name)
        if value is None:
            return

        value = python.force_list(value)
        for sub_value in value:
            if sub_value:
                tp.Dcc.store_world_matrix_to_attribute(sub_value, skip_if_exists=True)

            return value

    def _post_add_to_control_set(self):
        """
        Adds rig controls to default controls set
        """

        set_name = 'set_controls'
        exists = False
        if tp.Dcc.object_exists(set_name) and tp.Dcc.node_type(set_name) == 'objectSet':
            exists = True
        if not exists:
            sets = tp.Dcc.get_selection_groups(name='{}*'.format(set_name))
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
            tp.Dcc.add_node_to_selection_group(custom_set_name, parent_set, force=False)
            parent_set = custom_set_name

        if self.__class__ != Rig:
            child_set = 'set_{}'.format(self._description)
            if self._side:
                child_set = 'set_{}_{}'.format(self._description, self._side)
            if child_set != parent_set:
                if not tp.Dcc.object_exists(child_set):
                    tp.Dcc.create_selection_group(name=child_set, empty=True)
                tp.Dcc.add_node_to_selection_group(child_set, parent_set, force=False)

        if not child_set:
            child_set = parent_set

        controls = self.get_all_controls()
        for ctrl in controls:
            tpRigToolkit.logger.info('Adding control: {} to control sets'.format(ctrl))
            tp.Dcc.add_node_to_selection_group(ctrl, child_set, force=False)

    def _post_connect_controller(self):
        """
        Internal function that is called one controller has been connected (only for Maya)
        """

        if not tp.is_maya():
            return

        controller = tp.Dcc.get_message_input(self._controls_group, 'control1')
        if not self._pick_walk_parent:
            parent = tp.Dcc.node_parent(self._controls_group)
            if not parent:
                return
        else:
            parent = self._pick_walk_parent

        if controller:
            if not maya.cmds.controller(parent, query=True, isController=True):
                return
            else:
                maya.cmds.controller(controller, parent, p=True)

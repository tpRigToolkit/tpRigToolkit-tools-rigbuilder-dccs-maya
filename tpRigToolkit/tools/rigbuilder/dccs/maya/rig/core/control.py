#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig implementations for tpRigToolkits-tools-rigbuilder-dccs-maya
"""

from __future__ import print_function, division, absolute_import

import string
from collections import OrderedDict

import tpDcc as tp
from tpDcc.libs.python import settings

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.core import controls


class ControlName(object):
    def __init__(self):
        self._control_alias = 'CNT'
        self._center_alias = 'C'
        self._left_alias = 'L'
        self._right_alias = 'R'
        self._control_order = ['Control Alias', 'Description', 'Number', 'Side']
        self._control_uppercase = False
        self._control_number = True

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def control_alias(self):
        return self._control_alias

    @control_alias.setter
    def control_alias(self, value):
        self._control_alias = str(value)

    @property
    def center_alias(self):
        return self._center_alias

    @center_alias.setter
    def center_alias(self, value):
        self._center_alias = str(value)

    @property
    def left_alias(self):
        return self._left_alias

    @left_alias.setter
    def left_alias(self, value):
        self._left_alias = str(value)

    @property
    def right_alias(self):
        return self._right_alias

    @right_alias.setter
    def right_alias(self, value):
        self._right_alias = str(value)

    @property
    def control_order(self):
        return self._control_order

    @control_order.setter
    def control_order(self, value):
        self._control_order = value

    @property
    def uppercase(self):
        return self._control_uppercase

    @uppercase.setter
    def uppercase(self, flag):
        self._control_uppercase = flag

    @property
    def control_number(self):
        return self._control_number

    @control_number.setter
    def control_number(self, value):
        self._control_number = value

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_name(self, description, side=None):
        """
        Returns a proper name for the control taking into account current defined attributes
        :param description: str
        :param side: str
        :return: str
        """

        found = list()

        if not self._control_order:
            return
        for name in self._control_order:
            if name == 'Control Alias':
                found.append(self._control_alias)
            elif name == 'Description':
                found.append(description)
            elif name == 'Number' and self._control_number is True:
                found.append(str(1))
            elif name == 'Side':
                if tp.Dcc.name_is_center(side):
                    found.append(self._center_alias)
                elif tp.Dcc.name_is_left(side):
                    found.append(self._left_alias)
                elif tp.Dcc.name_is_right(side):
                    found.append(self._right_alias)

        full_name = string.join(found, '_')

        if self._control_uppercase:
            full_name = full_name.upper()

        return full_name


class ControlNameFromFile(ControlName, object):
    def __init__(self, directory=None):
        super(ControlNameFromFile, self).__init__()

        self._directory = directory
        self._settings_inst = None

        if directory:
            self.set_directory(directory)

    def set_directory(self, directory, filename='settings.json'):
        """
        Sets the directory where control name file settings file is located
        :param directory: str
        :param filename: str
        """

        self._directory = directory
        settings_inst = settings.JSONSettings()
        settings_inst.set_directory(directory, filename)
        self._settings_inst = settings_inst

        control_order = settings_inst.get('control_name_order')
        if control_order:
            self._control_order = control_order

        self._center_alias = settings_inst.get('control_center')
        self._control_alias = settings_inst.get('control_alias')
        self._left_alias = settings_inst.get('control_left')
        self._right_alias = settings_inst.get('control_right')

        if not self._control_alias:
            self._control_alias = 'CNT'
        if not self._left_alias:
            self._left_alias = 'L'
        if not self._right_alias:
            self._right_alias = 'R'
        elif not self._center_alias:
            self._center_alias = 'C'

        self._control_uppercase = settings_inst.get('control_uppercase')
        if self._control_uppercase is None:
            self._control_uppercase = True

    def set(self, name, value):

        update_settings = True
        value_to_store = value
        if name == 'control_name_order':
            self._control_order = value
        elif name == 'control_alias':
            value_to_store = str(value)
            self._control_alias = value_to_store
        elif name == 'control_center':
            self._center_alias = value
        elif name == 'control_left':
            self._left_alias = value
        elif name == 'control_right':
            self._right_alias = value
        elif name == 'control_uppercase':
            self._control_uppercase = value
        else:
            update_settings = False

        if update_settings and self._settings_inst:
            self._settings_inst.set(name, value_to_store)


class Control(object):
    def __init__(self, name, tag=True):
        self._control = name
        self._curve_type = None
        self._control_data = OrderedDict()

        if not tp.Dcc.object_exists(self._control):
            self._create(tag)

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        if not self._shapes:
            tpRigToolkit.logger.warning('{} has no shapes'.format(self._control))

    @staticmethod
    def rename_control(old_name, new_name):
        """
        Renames given control with the given new_name
        :param old_name: str
        :param new_name: str
        :return: str
        """

        new_name = Control(old_name).rename(new_name)
        return new_name

    @property
    def control(self):
        return self._control

    def get(self):
        """
        Returns dcc scene node
        :return: str
        """

        return self._control

    def set_curve_type(self, type_name):
        """
        Sets the curve type of the control
        :param type_name: str
        """

        self._update_controls_data()

        shapes = tp.Dcc.list_shapes_of_type(self._control)
        color = tp.Dcc.node_color(shapes[0])

        item = self._control_data[type_name]
        ccs = controls.RigBuilderControlLib().create_control(
            shape_data=item.shapes,
            target_object=self._control,
            size=5.0,
            name='ctrl_temp',
            shape_parent=True
        )
        controls.RigBuilderControlLib().set_shape(self._control, ccs)

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        tp.Dcc.set_node_color(self._shapes, color)

    def color(self, value):
        """
        Sets the color of the curve
        :param value: int, corresponds to Maya's color overide value
        """

        shapes = tp.Dcc.list_shapes_of_type(self._control)
        tp.Dcc.set_node_color(shapes, value)

    def color_rgb(self, r=0, g=0, b=0):
        """
        Sets the color of the curve by its RGB components. Available for Maya 2015 and above
        :param r: float
        :param g: float
        :param b: float
        """

        shapes = tp.Dcc.list_shapes_of_type(self._control)
        tp.Dcc.set_node_color(shapes, [r, g, b])

    def rename(self, new_name):
        """
        Sets a new name to the control
        :param new_name: str
        """

        new_name = tp.Dcc.find_unique_name(new_name)
        self._rename_message_groups(self._control, new_name)
        new_name = tp.Dcc.rename_node(self._control, new_name)
        constraints = tp.Dcc.node_constraints(new_name)
        if constraints:
            for cns in constraints:
                new_cns = cns.replace(self._control, new_name)
                tp.Dcc.rename_node(cns, new_cns)

        self._control = new_name
        tp.Dcc.rename_transform_shape_nodes(self._control)

        return self._control

    def copy_shapes(self, transform):
        """
        Copies current shapes into given transform
        :param transform: str
        """

        if not tp.Dcc.node_has_shape_of_type(self._control, shape_type='nurbsCurve'):
            return

        orig_shapes = tp.Dcc.list_shapes_of_type(self._control, shape_type='nurbsCurve')
        temp = tp.Dcc.duplicate_object(transform)
        tp.Dcc.set_parent(temp, self._control)
        tp.Dcc.freeze_transforms(temp, translate=True, rotate=True, scale=True)
        shapes = tp.Dcc.list_shapes_of_type(temp, shape_type='nurbsCurve')
        colors = dict()
        if shapes:
            for i, shape in enumerate(shapes):
                if i < len(orig_shapes) and i < len(shapes):
                    color = tp.Dcc.node_color(orig_shapes[i])
                colors[shape] = color
                if color:
                    tp.Dcc.set_node_color(shape, color)
                tp.Dcc.parent_shape_to_transform(shape, self._control)
                tp.Dcc.set_shape_parent(shape, self._control)

        tp.Dcc.delete_object(orig_shapes)
        tp.Dcc.delete_object(temp)

        tp.Dcc.rename_transform_shape_nodes(self._control)

    def delete_shapes(self):
        """
        Deletes teh shapes of this control
        """

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        tp.Dcc.delete_object(self._shapes)
        self._shapes = list()

    # =============================================================================================
    # ATTRIBUTES
    # =============================================================================================

    def show_translate_attributes(self):
        """
        Unlock and set keyable the control translate attributes
        """

        for axis in 'XYZ':
            tp.Dcc.unlock_attribute(self._control, 'translate{}'.format(axis))
            tp.Dcc.keyable_attribute(self._control, 'translate{}'.format(axis))

    def show_rotate_attributes(self):
        """
        Unlock and set keyable the control rotate attributes
        """

        for axis in 'XYZ':
            tp.Dcc.unlock_attribute(self._control, 'rotate{}'.format(axis))
            tp.Dcc.keyable_attribute(self._control, 'rotate{}'.format(axis))

    def show_scale_attributes(self):
        """
        Unlock and set keyable the control scale attributes
        """

        for axis in 'XYZ':
            tp.Dcc.unlock_attribute(self._control, 'scale{}'.format(axis))
            tp.Dcc.keyable_attribute(self._control, 'scale{}'.format(axis))

    def hide_attributes(self, attributes=None):
        """
        Lock and hide the given attributes on the control. If no attributes given, hide translate, rotate, scale and visibility
        :param attributes: list<str>, list of attributes to hide and lock (['translateX', 'translateY'])
        """

        if attributes:
            tp.Dcc.hide_attributes(self._control, attributes)
        else:
            self.hide_translate_attributes()
            self.hide_rotate_attributes()
            self.hide_scale_and_visibility_attributes()

    def hide_translate_attributes(self):
        """
        Lock and hide the translate attributes on the control
        """

        tp.Dcc.lock_translate_attributes(self._control)
        tp.Dcc.hide_translate_attributes(self._control)

    def hide_rotate_attributes(self):
        """
        Lock and hide the rotate attributes on the control
        """

        tp.Dcc.lock_rotate_attributes(self._control)
        tp.Dcc.hide_rotate_attributes(self._control)

    def hide_scale_attributes(self):
        """
        Lock and hide the scale attributes on the control
        """

        tp.Dcc.lock_scale_attributes(self._control)
        tp.Dcc.hide_scale_attributes(self._control)

    def hide_visibility_attribute(self):
        """
        Lock and hide the visibility attribute on the control
        """

        tp.Dcc.lock_visibility_attribute(self._control)
        tp.Dcc.hide_visibility_attribute(self._control)

    def hide_scale_and_visibility_attributes(self):
        """
        lock and hide the visibility and scale attributes on the control
        """

        self.hide_scale_attributes()
        self.hide_visibility_attribute()

    def hide_keyable_attributes(self):
        """
        Lock and hide all keyable attributes on the control
        """

        tp.Dcc.lock_keyable_attributes(self._control)
        tp.Dcc.hide_keyable_attributes(self._control)

    # ==============================================================================================
    # TRANSFORM
    # ==============================================================================================

    def translate_shape(self, x, y, z):
        """
        Translates the shape curve CVS in object space
        :param x: float
        :param y: float
        :param z: float
        """

        components = self._get_components()
        if components:
            tp.Dcc.move_node(components, x, y, z, relative=True, object_space=True, world_space_distance=True)

    def rotate_shape(self, x, y, z):
        """
        Rotates the shape curve CVS in object space
        :param x: float
        :param y: float
        :param z: float
        """

        components = self._get_components()
        if components:
            tp.Dcc.rotate_node(components, x, y, z, relative=True)

    def scale_shape(self, x, y, z, use_pivot=True):
        """
        Scales teh shape curve CVS relative to the current scale
        :param x: float
        :param y: float
        :param z: float
        :param use_pivot: bool
        """

        components = self._get_components()
        if use_pivot:
            pivot = tp.Dcc.node_world_space_pivot(self._control)
        else:
            pivot = tp.Dcc.node_bounding_box_pivot(self._control)

        if components:
            tp.Dcc.scale_node(components, x, y, z, pivot=pivot, relative=True)


    # ==============================================================================================
    # PRIVATE
    # ==============================================================================================

    def _create(self, tag=True):
        """
        Internal function that creates current control
        :param tag: bool
        :return: Control
        """

        if tp.is_maya():
            import tpDcc.dccs.maya as maya

        self._control = tp.Dcc.create_circle_curve(name=self._control)
        if self._curve_type:
            self.set_curve_type(self._curve_type)

        if tag:
            if tp.is_maya():
                try:
                    maya.cmds.controller(self._control)
                except Exception as exc:
                    tpRigToolkit.logger.warning('Impossible to setup control controller: {}'.format(exc))

    def _get_components(self):
        """
        Internal function that returns curve components
        :return:
        """

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        return tp.Dcc.node_components(self._shapes)

    def _update_controls_data(self):
        """
        Internal function that updates controls data info
        """

        ctrls_list = list()
        for ctrl in controls.RigBuilderControlLib().get_controls():
            ctrls_list.append(ctrl.name)
            self._control_data[ctrl.name] = ctrl
        ctrls_name = ':'.join(ctrls_list)

        return ctrls_name

    def _rename_message_groups(self, search_name, replace_name):
        """
        Internal function that renames message attributes linked to this control
        :param search_name: str
        :param replace_name: str
        """

        message_attrs = tp.Dcc.get_message_attributes(search_name)
        if not message_attrs:
            return

        for attr_name in message_attrs:
            attr_node = '{}.{}'.format(search_name, attr_name)
            if attr_name.endswith('group'):
                node = tp.Dcc.get_attribute_input(attr_node, node_only=True)
                if node.find(search_name) > -1:
                    new_node = node.replace(search_name, replace_name)
                    self._rename_message_groups(node, new_node)
                    constraints = tp.Dcc.node_constraints(node)
                    if constraints:
                        for cns in constraints:
                            new_constraint = cns.replace(node, new_node)
                            tp.Dcc.rename_node(cns, new_constraint)

                    tp.Dcc.rename_node(node, new_node)

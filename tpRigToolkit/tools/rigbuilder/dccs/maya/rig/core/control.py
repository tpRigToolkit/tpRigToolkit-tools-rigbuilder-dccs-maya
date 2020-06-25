#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig implementations for tpRigToolkits-tools-rigbuilder for Maya
"""

from __future__ import print_function, division, absolute_import

from collections import OrderedDict

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.core import controls

import tpDcc as tp


class RigControl(object):

    ROTATE_ORDER = {
        'xyz': 0,
        'yzx': 1,
        'zxy': 2,
        'xzy': 3,
        'yxz': 4,
        'zyx': 5
    }

    def __init__(self, name, tag=True):
        self._control = name
        self._curve_type = 'circle'
        self._control_data = OrderedDict()

        if not tp.Dcc.object_exists(self._control):
            self._create(tag=tag)

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        if not self._shapes:
            tpRigToolkit.logger.warning('{} has no shapes'.format(self._control))

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    def control(self):
        return self._control

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get(self):
        """
        Returns dcc scene node
        :return: str
        """

        return self._control

    def get_buffer_group(self):
        """
        Returns buffer group of this control
        :return:
        """

        return tp.Dcc.get_buffer_group(self._control)

    def rename(self, new_name):
        """
        Gives a new name to the control
        :param new_name: str
        """

        new_name = tp.Dcc.find_unique_name(new_name)
        self._rename_message_groups(self._control, new_name)
        new_name = tp.Dcc.rename_node(self._control, new_name)
        constraints = tp.Dcc.list_constraints(new_name)
        if constraints:
            for constraint in constraints:
                new_constraint = constraint.replace(self._control, new_name)
                tp.Dcc.rename_node(constraint, new_constraint)

        self._control = new_name
        tp.Dcc.rename_shapes(self._control)

        return self._control

    def set_curve_type(self, type_name):
        """
        Sets the curve type of the control
        :param type_name: str
        """

        shapes = tp.Dcc.list_shapes_of_type(self._control)
        color = tp.Dcc.node_color(shapes[0])

        ctrl_data = controls.RigBuilderControlLib().get_control_data_by_name(type_name)
        control_shapes = controls.RigBuilderControlLib().create_control(
            shape_data=ctrl_data.shapes,
            target_object=self._control,
            size=5.0,
            name='ctrl_temp',
            shape_parent=True,
            color=color
        )
        controls.RigBuilderControlLib().set_shape(self._control, control_shapes)

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        self._curve_type = type_name

    def set_color(self, color):
        """
        Sets the color of the control
        :param color: int or list(float, float, float) or QColor
        """

        shapes = tp.Dcc.list_shapes_of_type(self._control)
        tp.Dcc.set_node_color(shapes, color)

    def set_rotate_order(self, rotate_order):
        """
        Sets the rotate of the control
        :param rotate_order: str ('xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx')
        """

        if type(rotate_order) in [int, float]:
            value = int(rotate_order)
        else:
            value = self.ROTATE_ORDER.get(rotate_order, 0)

        tp.Dcc.set_attribute_value(self._control, 'rotateOrder', value)

    def set_data(self, data_dict):
        """
        Function that sets control attributes using the contents of a dictionary
        :param data_dict: dict
        """

        control_name = data_dict.get('control_name', None)
        curve_type = control_name or self._curve_type

        ctrl_data = controls.RigBuilderControlLib().get_control_data_by_name(curve_type)
        control_shapes = controls.RigBuilderControlLib().create_control(
            shape_data=ctrl_data.shapes,
            target_object=self._control,
            **data_dict
        )
        size = data_dict.get('size', None)
        controls.RigBuilderControlLib().set_shape(self._control, control_shapes, size=size)

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)

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

    def create_buffer(self):
        """
        Creates a buffer group above the current control
        :return: str
        """

        buffer_group = tp.Dcc.create_buffer_group(self._control)

        return buffer_group

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
    # INTERNAL
    # ==============================================================================================

    def _create(self, tag=True):
        self._control = tp.Dcc.create_circle_curve(name=self._control)
        if self._curve_type:
            self.set_curve_type(self._curve_type)

        if tag and tp.is_maya():
            import tpDcc.dccs.maya as maya
            try:
                maya.cmds.controller(self._control)
            except Exception as exc:
                tpRigToolkit.logger.warning(
                    'Impossible to setup control "{}" controller: {}'.format(self._control, exc))

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

    def _get_components(self):
        """
        Internal function that returns curve components
        :return:
        """

        self._shapes = tp.Dcc.list_shapes_of_type(self._control)
        return tp.Dcc.node_components(self._shapes)

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
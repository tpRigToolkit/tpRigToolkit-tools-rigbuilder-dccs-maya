#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains build node implementation for simple Ik legs
"""

from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.objects import component
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.modules import iklimbrig


class SimpleIkChain(component.ChainComponent, object):

    COLOR = [180, 100, 95]
    SHORT_NAME = 'IK '
    DESCRIPTION = 'Creates a simple IK setup'
    ICON = 'new'

    def __init__(self, name=None, rig=None):
        super(SimpleIkChain, self).__init__(name=name, rig=rig)

    def setup_options(self):
        setup_options = super(SimpleIkChain, self).setup_options()

        setup_options['Ik'] = {'value': True, 'group': None, 'type': 'group'}
        setup_options['Ik Chain'] = {'value': None, 'group': 'Ik', 'type': 'boneList'}

        setup_options['Create Pole Vector Control'] = {'value': True, 'group': 'Ik', 'type': 'bool'}
        setup_options['Create Top Control'] = {'value': True, 'group': 'Ik', 'type': 'bool'}
        setup_options['Pole Vector Control'] = {'value': None, 'group': 'Ik', 'type': 'rigcontrol'}
        setup_options['Top Control'] = {'value': None, 'group': 'Ik', 'type': 'rigcontrol'}
        setup_options['Bottom Control'] = {'value': None, 'group': 'Ik', 'type': 'rigcontrol'}
        setup_options['Pole Vector Offset'] = {'value': None, 'group': 'Ik', 'type': 'float'}

        return setup_options

    def run(self, *args, **kwargs):
        super(SimpleIkChain, self).run(*args, **kwargs)

        description = self.get_option('Component Description', group='Inputs', default='IkLimb')
        mirror = self.get_option('Mirror', group='Inputs', default=False)
        use_side_colors = self.get_option('Use Side Colors', group='Inputs', default=True)
        ik_chain = self.get_option('Ik Chain', group='Ik')
        create_pole_vector_control = self.get_option('Create Pole Vector Control', group='Ik')
        create_top_control = self.get_option('Create Top Control', group='Ik')
        pole_vector_control_data = self.get_option('Pole Vector Control', group='Ik')
        top_control_data = self.get_option('Top Control', group='Ik')
        bottom_control_data = self.get_option('Bottom Control', group='Ik')
        pole_vector_control_offset = self.get_option('Pole Vector Offset', group='Ik', default=1.0)

        parent_component = self.get_parent_component()
        control_size = self.get_controls_size()

        mirror_side = api.get_mirror_side()
        mirror = mirror if not parent_component else mirror or parent_component.get_mirror()
        sides = api.get_sides(skip_default=True)[0] if mirror else [api.get_default_side()]

        for side in sides:
            mirror_rig = mirror and side == mirror_side
            joints = self._get_joints(mirror_rig, ik_chain)
            rig = iklimbrig.IkLimbRig(description=description, side=side)
            rig.set_mirror(mirror_rig)
            rig.set_joints(joints)
            rig.set_create_switch(self.get_create_switch())
            rig.set_switch_attribute_name(self.get_switch_attribute())
            rig.set_auto_switch_visibility(self.get_auto_switch_visibility())
            rig.set_attach_type(self.get_attach_type())
            rig.set_buffer(self.get_duplicate_hierarchy())
            rig.set_enable_attach_joints(self.get_attach_chain())
            rig.set_control_size(control_size)
            rig.set_buffer_replace('joint', 'ik')
            rig.set_use_side_colors(use_side_colors)
            rig.set_create_pole_vector_control(create_pole_vector_control)
            rig.set_create_top_control(create_top_control)
            rig.set_pole_vector_control_data(pole_vector_control_data)
            rig.set_top_control_data(top_control_data)
            rig.set_bottom_control_data(bottom_control_data)
            rig.set_pole_vector_control_offset(pole_vector_control_offset)
            rig.create()
            self._setup_rig(side, rig, joints)

        return True

    def _get_joints(self, mirror, ik_chain):
        joints = ik_chain
        if mirror:
            joints = [api.get_mirror_name(joint_name) for joint_name in joints]

        return joints

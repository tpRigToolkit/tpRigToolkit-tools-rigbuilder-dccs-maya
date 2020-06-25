#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains build node implementation for simple Fk Chain
"""

from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.objects import component
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.modules import fkrig


class SimpleFkChain(component.ChainComponent, object):

    COLOR = [123, 80, 45]
    SHORT_NAME = 'FK'
    DESCRIPTION = 'Creates a simple FK Chain setup'
    ICON = 'new'

    def __init__(self, name=None, rig=None):
        super(SimpleFkChain, self).__init__(name=name, rig=rig)

    def setup_options(self):
        setup_options = super(SimpleFkChain, self).setup_options()

        setup_options['Fk'] = {'value': True, 'group': None, 'type': 'group'}
        setup_options['Fk Chain'] = {'value': None, 'group': 'Fk', 'type': 'boneControlLink'}
        setup_options['Match Controls Rotation'] = {'value': True, 'group': 'Fk', 'type': 'bool'}

        return setup_options

    def run(self, *args, **kwargs):
        super(SimpleFkChain, self).run(*args, **kwargs)

        description = self.get_option('Component Description', group='Inputs', default='FkSpine')
        mirror = self.get_option('Mirror', group='Inputs', default=False)
        use_side_colors = self.get_option('Use Side Colors', group='Inputs', default=True)
        fk_chain = self.get_option('Fk Chain', group='Fk')
        create_switch = self.get_option('Create Switch', group='Fk', default=True)
        match_controls_rotation = self.get_option('Match Controls Rotation', group='Fk')
        duplicate_hierarchy = self.get_option('Duplicate Hierarchy', group='Fk', default=False)
        attach_chain = self.get_option('Attach Chain', group='Fk', default=True)
        controls = [fk_link['control'] for fk_link in fk_chain]

        parent_component = self.get_parent_component()
        control_size = self.get_controls_size()

        mirror_side = api.get_mirror_side()
        mirror = mirror if not parent_component else mirror or parent_component.get_mirror()
        sides = api.get_sides(skip_default=True)[0] if mirror else [api.get_default_side()]

        for side in sides:
            mirror_rig = mirror and side == mirror_side
            joints = self._get_joints(mirror_rig, fk_chain)
            rig = fkrig.FkRig(description=description, side=side)
            rig.set_mirror(mirror_rig)
            rig.set_joints(joints)
            rig.set_control_size(control_size)
            rig.set_create_switch(create_switch)
            rig.set_switch_attribute_name(self.get_switch_attribute())
            rig.set_auto_switch_visibility(self.get_auto_switch_visibility())
            rig.set_attach_type(self.get_attach_type())
            rig.set_buffer_replace('joint', 'fk')
            rig.set_match_to_rotation(match_controls_rotation)
            rig.set_use_side_colors(use_side_colors)
            rig.set_buffer(duplicate_hierarchy)
            rig.set_enable_attach_joints(attach_chain)
            for index, ctrl_data in enumerate(controls):
                rig.set_control_data(ctrl_data, index=index)
            rig.create()
            self._setup_rig(side, rig, joints)

        return True

    def _get_joints(self, mirror, fk_chain):
        joints = [fk_link['node'] for fk_link in fk_chain]
        if mirror:
            joints = [api.get_mirror_name(joint_name) for joint_name in joints]

        return joints

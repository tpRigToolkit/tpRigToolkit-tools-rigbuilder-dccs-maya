#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains build node implementation for god rig component
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp

from tpRigToolkit.tools.rigbuilder.objects import component
from tpRigToolkit.tools.rigbuilder.dccs.maya.rig.modules import controlrig


class GodRig(component.RigComponent, object):

    COLOR = [215, 235, 45]
    SHORT_NAME = 'GOD'
    DESCRIPTION = 'Creates God Rig setup'
    ICON = 'new'

    def __init__(self, name=None, rig=None):
        super(GodRig, self).__init__(name=name, rig=rig)

    def setup_options(self):
        setup_options = super(GodRig, self).setup_options()

        setup_options['God'] = {'value': True, 'group': None, 'type': 'group'}
        setup_options['Main Control'] = {'value': None, 'group': 'God', 'type': 'rigcontrol'}
        setup_options['Match Node'] = {'value': None, 'group': 'God', 'type': 'bone'}

        return setup_options

    def run(self, *args, **kwargs):
        super(GodRig, self).run(*args, **kwargs)

        description = self.get_option('Component Description', group='Inputs', default='god')
        main_control = self.get_option('Main Control', group='God')
        match_node = self.get_option('Match Node', group='God')

        control_size = self.get_controls_size()
        controls_grp = self.get_controls_group()

        rig = controlrig.ControlRig(description=description)
        rig.set_control_data(main_control)
        rig.set_control_size(control_size)
        rig.create()

        rig.set_control_parent(controls_grp)
        rig.delete_setup()

        rig_control = rig.controls[0]
        control_buffer = rig.get_control_buffer(rig_control)
        match_xform = control_buffer if control_buffer and tp.Dcc.object_exists(control_buffer) else rig_control
        if match_xform and tp.Dcc.object_exists(match_xform) and match_node and tp.Dcc.object_exists(match_node):
            tp.Dcc.match_translation_rotation(match_node, match_xform)

        return True

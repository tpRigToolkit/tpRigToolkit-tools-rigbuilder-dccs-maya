#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains build node implementation for simple Fk Chain
"""

import tpDcc as tp
from tpDcc.dccs.maya.core import rig as rig_utils, constraint as cns_utils

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.dccs.maya.packages.mayarig.nodes import rigNode


class SimpleFkIkChain(rigNode.RigNode, object):

    COLOR = [235, 125, 90]
    SHORT_NAME = 'FK/IK'
    DESCRIPTION = 'Creates a simple FK/IK Switch Setup'
    ICON = 'new'

    def __init__(self, name=None, rig=None):
        super(SimpleFkIkChain, self).__init__(name=name, rig=rig)

    def setup_options(self):
        setup_options = super(SimpleFkIkChain, self).setup_options()

        setup_options['Switch'] = {'value': True, 'group': None, 'type': 'group'}
        setup_options['Attach Type'] = {'value': ['Constraint', 'Matrix'], 'group': 'Switch', 'type': 'combo'}
        setup_options['Switch Attribute'] = {'value': 'fkIk', 'group': 'Switch', 'type': 'string'}
        setup_options['Auto Switch Visibility'] = {'value': True, 'group': 'Switch', 'type': 'bool'}

        return setup_options

    def pre_run(self, *args, **kwargs):
        super(SimpleFkIkChain, self).pre_run(*args, **kwargs)

        switch_attribute = self.get_option('Switch Attribute', group='Switch', default='fkIk')
        attach_type = self.get_option('Attach Type', group='Switch')
        auto_switch_visibility = self.get_option('Auto Switch Visibility', group='Switch', default=True)
        attach_type_index = attach_type[0] if attach_type else 0

        # We force all children components to enable duplicate hierarchy functionality
        children_components = self.get_children_components()
        for children_component in children_components:
            if children_component.has_option('Duplicate Hierarchy', 'Chain'):
                children_component.set_option('Duplicate Hierarchy', True, group='Chain')
            elif hasattr(children_component, 'set_duplicate_hierarchy'):
                children_component.set_duplicate_hierarchy(True)
            else:
                tpRigToolkit.logger.error(
                    'Not valid switch children component found. No Duplicate Hierarchy option or set_'
                    'duplicate_hierarchy function defined: {}'.format(children_component))
                return False

            if children_component.has_option('Attach Chain', 'Chain'):
                children_component.set_option('Attach Chain', True, group='Chain')
            elif hasattr(children_component, 'set_attach_chain'):
                children_component.set_attach_chain(True)
            else:
                tpRigToolkit.logger.error(
                    'Not valid switch children component found. No Attach Chain option or set_'
                    'attach_chain function defined: {}'.format(children_component))
                return False

            if children_component.has_option('Create Switch', 'Chain'):
                children_component.set_option('Create Switch', True, group='Chain')
            elif hasattr(children_component, 'set_create_switch'):
                children_component.set_create_switch(True)
            else:
                tpRigToolkit.logger.error(
                    'Not valid switch children component found. No Create Switch option or set_'
                    'create_switch function defined: {}'.format(children_component))
                return False

            if hasattr(children_component, 'set_switch_attribute'):
                children_component.set_switch_attribute(switch_attribute)
            else:
                tpRigToolkit.logger.error(
                    'Not valid switch children component found. No set_switch_attribute function defined: {}'.format(
                        children_component))
                return False

            if hasattr(children_component, 'set_attach_type'):
                children_component.set_attach_type(attach_type_index)
            else:
                tpRigToolkit.logger.error(
                    'Not valid switch children component found. No set_attach_type function defined: {}'.format(
                        children_component))
                return False

            if hasattr(children_component, 'set_auto_switch_visibility'):
                children_component.set_auto_switch_visibility(auto_switch_visibility)
            else:
                tpRigToolkit.logger.error(
                    'Not valid switch children component found. No set_auto_switch_visibility '
                    'function defined: {}'.format(children_component))
                return False

        return True

    def post_run(self, *args, **kwargs):
        super(SimpleFkIkChain, self).post_run(*args, **kwargs)

        # NOTE: We consider first element as the Fk chain and the second one as Ik chain
        # TODO: Find a better way of finding this info (maybe by checkin component class name?)

        children_components = self.get_children_components()
        if len(children_components) != 2:
            tpRigToolkit.logger.error(
                '{} component only can switch between 2 chain components!'.format(self.__class__.__name__))
            return False

        fk_component = children_components[0]
        ik_component = children_components[1]

        mirror = self.get_mirror()
        sides = api.get_sides(skip_default=True)[0] if mirror else [api.get_default_side()]

        for side in sides:
            fk_joints = fk_component.get_chain_joints(side=side)
            ik_joints = ik_component.get_chain_joints(side=side)
            if fk_joints != ik_joints:
                tpRigToolkit.logger.error(
                    '{} component source chains are not the same: {} | {}'.format(
                        self.__class__.__name__, fk_joints, ik_joints))
                return False

        return True

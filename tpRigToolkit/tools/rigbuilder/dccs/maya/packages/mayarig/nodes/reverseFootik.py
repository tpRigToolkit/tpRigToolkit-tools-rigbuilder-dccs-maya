#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains build node implementation for simple Ik legs
"""

import tpDcc as tp

import tpRigToolkit
from tpRigToolkit.tools.rigbuilder.core import api
from tpRigToolkit.tools.rigbuilder.objects import component


class ReverseFootIk(component.RigComponent, object):

    COLOR = [34, 180, 95]
    SHORT_NAME = 'REV'
    DESCRIPTION = 'Creates Reverse Foot IK setup'
    ICON = 'new'

    def __init__(self, name=None, rig=None):
        super(ReverseFootIk, self).__init__(name=name, rig=rig)

    def run(self, **kwargs):
        mirror = self.get_option('Mirror', group='Inputs', default=False)
        joints = self.get_option('Joints', group='Inputs')

        sides = ['left'] if not mirror else ['left', 'right']

        for side in sides:
            valid_joints = True
            if len(joints) != 3:
                tpRigToolkit.logger.warning(
                    'Reverse Foot Ik Setup requires to define 3 joints ({} defined)'.format(len(joints)))
                return False
            start_jnt, mid_jnt, end_jnt = joints
            start_jnt_name = api.solve_name(start_jnt, node_type='joint', side=side)
            mid_jnt_name = api.solve_name(mid_jnt, node_type='joint', side=side)
            end_jnt_name = api.solve_name(end_jnt, node_type='jointEnd', side=side)
            for jnt in [start_jnt_name, mid_jnt_name, end_jnt_name]:
                if not tp.Dcc.object_exists(jnt):
                    tpRigToolkit.logger.warning('Joint "{}" does not exists in current scene!'.format(jnt))
                    valid_joints = False
                    continue
            if not valid_joints:
                return False

            ik_handle_name_1 = api.solve_name('ball', node_type='ikSCsolver', side=side)
            ik_handle_name_2 = api.solve_name('toe', node_type='ikSCsolver', side=side)
            tp.Dcc.create_ik_handle(
                ik_handle_name_1, start_joint=start_jnt_name, end_joint=mid_jnt_name, solver_type='ikSCsolver')
            tp.Dcc.create_ik_handle(
                ik_handle_name_2, start_joint=mid_jnt_name, end_joint=end_jnt_name, solver_type='ikSCsolver')

        return True

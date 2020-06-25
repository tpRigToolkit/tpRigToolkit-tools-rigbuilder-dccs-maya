#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains build node implementation for basic rig component
"""

from __future__ import print_function, division, absolute_import

from tpRigToolkit.tools.rigbuilder.objects import component


class RigNode(component.RigComponent, object):

    COLOR = [45, 185, 45]
    SHORT_NAME = 'RIG'
    DESCRIPTION = 'Creates Core Rig setup'
    ICON = 'new'

    def __init__(self, name=None, rig=None):
        super(RigNode, self).__init__(name=name, rig=rig)

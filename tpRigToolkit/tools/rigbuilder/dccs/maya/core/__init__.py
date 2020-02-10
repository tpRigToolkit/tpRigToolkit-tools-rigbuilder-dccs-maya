#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpRigToolkit.tools.rigbuilder-dccs-maya-core
"""

from __future__ import print_function, division, absolute_import

import os


os.environ['MAYA_RIGBUILDER_PATH'] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

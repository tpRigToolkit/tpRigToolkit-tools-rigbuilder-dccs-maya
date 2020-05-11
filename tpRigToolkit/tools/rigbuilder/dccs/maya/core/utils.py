#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions and classes for tpRigToolkit.tools.rigbuilder-dccs-maya
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from tpDcc.libs.python import osplatform, path as path_utils


def get_maya_rig_builder_directory():
    """
    Returns RigBuilder directory
    :return: str
    """

    file_path = osplatform.get_env_var('MAYA_RIGBUILDER_PATH')
    file_path = path_utils.clean_path(file_path)

    return file_path


def get_data_files_directory():
    """
    Returns path where data files for tpRigToolkit.tools.rigbuilder are located
    :return: str
    """

    return os.path.join(get_maya_rig_builder_directory(), 'data')


def get_script_files_directory():
    """
    Returns path where script files for tpRigToolkit.tools.rigbuilder are located
    :return: str
    """

    return os.path.join(get_maya_rig_builder_directory(), 'scripts')

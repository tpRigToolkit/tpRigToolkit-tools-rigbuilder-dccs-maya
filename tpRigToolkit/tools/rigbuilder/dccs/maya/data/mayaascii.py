#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains data Maya ASCII widget
"""

from __future__ import print_function, division, absolute_import

import os
import time
import shutil
import locale
import getpass

from tpMayaLib.core import helpers
from tpMayaLib.data import base as maya_base

import tpDccLib as tp
from tpQtLib.widgets.library import utils
from tpPyUtils import timedate

from tpRigToolkit.core import resource
from tpRigToolkit.tools.rigbuilder.core import data


class MayaAsciiPreviewWidget(data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(MayaAsciiPreviewWidget, self).__init__(item=item, parent=parent)

    def ui(self):
        super(MayaAsciiPreviewWidget, self).ui()

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)


class MayaAsciiTransferObject(utils.TransferObject, object):

    # For Maya ASCII files we do not need to store objects data
    DEFAULT_DATA = {'metadata': {}}

    def data_to_save(self):
        """
        Overrides utils.TransferObject data_to_save function
        :return: dict
        """

        encoding = locale.getpreferredencoding()
        user = getpass.getuser()
        if user:
            user = user.decode(encoding)

        ctime = str(time.time()).split('.')[0]

        self.set_metadata('user', user)
        self.set_metadata('ctime', ctime)
        self.set_metadata('mayaVersion', str(tp.Dcc.get_version())),
        self.set_metadata('mayaSceneFile', tp.Dcc.scene_name())

        metadata = {'metadata': self.metadata()}
        data = self.dump(metadata)

        return data


class MayaAscii(data.DataItem, object):

    Extension = '.{}'.format(maya_base.MayaAsciiFileData.get_data_extension())
    Extensions = ['.{}'.format(maya_base.MayaAsciiFileData.get_data_extension())]
    MenuName = maya_base.MayaAsciiFileData.get_data_title()
    MenuIconPath = resource.ResourceManager().get('icons', 'maya_ascii_data.png')
    TypeIconPath = resource.ResourceManager().get('icons', 'maya_ascii_data.png')
    DataType = maya_base.MayaAsciiFileData.get_data_type()
    PreviewWidgetClass = MayaAsciiPreviewWidget

    def __init__(self, *args, **kwargs):
        super(MayaAscii, self).__init__(*args, **kwargs)

        self.set_transfer_class(MayaAsciiTransferObject)
        self.set_data_class(maya_base.MayaAsciiFileData)

    def context_menu(self, menu):
        """
        Overrides base data.DataItem context_menu function
        :return:
        """

        student_icon = resource.ResourceManager().icon('student')
        menu.addAction(student_icon, 'Clean Student License', self._on_clean_student_license)

    def transfer_object(self):
        """
        Overrides base data.DataItem transfer_object function
        Returns the transfer object used to read and write the data
        :return: TransferObject
        """

        # We override this function to make sure that metadata file is created during transfer object creation
        if not self._transfer_object:
            path = self.transfer_path()
            self._transfer_object = self.transfer_class().from_path(path, force_cration=True)

        return self._transfer_object

    def write(self, path, objects=None, icon_path="", sequence_path="", **options):
        """
        Overrides base.DataItem write function
        :param path: str
        :param objects: list(str)
        :param icon_path: str
        :param sequence_path:  str
        :param options: dict
        :return:
        """

        if icon_path:
            shutil.copyfile(icon_path, path+'/thumbnail.jpg')
        if sequence_path:
            shutil.move(sequence_path, path+'/sequence')

        comment = options.get('comment', '-')
        name = options.get('name', 'new_maya_asii_file')

        # We use the data object to store the proper data
        data_object = self.data_object(name=name, path=path)
        return data_object.save(comment=comment, create_version=False)

    def save(self, path=None, *args, **kwargs):
        """
        Overrides base.DataItem write function
        :param path: str
        :param args: list
        :param kwargs: dict
        """

        super(MayaAscii, self).save(path=path, *args, **kwargs)

        # In Maya ASCII files we use the transfer object only to store metadata
        # NOTE: We must do this call here because if not we will try store the file in an non valid path
        # NOTE: because during save function all data is stored in a temporal folder until the creation process
        # is valid
        self.transfer_object().save(path=self.transfer_path())

    def _on_clean_student_license(self):
        """
        Internal callback function that is triggered when user presses Clean Student License action
        """

        file_path = os.path.join(self.path(), self.name())
        if not os.path.isfile(file_path):
            return

        if not helpers.file_has_student_line(file_path):
            return False

        valid_clean = helpers.clean_student_line(file_path)

        return valid_clean

    def info(self):
        """
        Returns the info to display to the user
        :return: list(dict)
        """

        ctime = self.ctime()
        if ctime:
            ctime = timedate.time_ago(ctime)

        return [
            {
                'name': 'name',
                'value': self.name()
            },
            {
                "name": "owner",
                "value": self.owner(),
            },
            {
                "name": "created",
                "value": ctime,
            },
            {
                "name": "comment",
                "value": self.description() or "No comment",
            },
        ]

    # def get_properties_widget(self):
    #     return MayaAsciiInfoWidget(data_widget=self)
    # # endregion


# class MayaAsciiInfoWidget(data_maya_base.MayaInfoWidget, object):
#     def __init__(self, data_widget, parent=None):
#         super(MayaAsciiInfoWidget, self).__init__(data_widget, parent)
#
#     # region Override Functions
#     def get_main_tab_name(self):
#         return 'Maya ASCII'
#
#     def get_save_widget(self):
#         return data_maya_base.MayaSaveFileWidget()
    # endregion


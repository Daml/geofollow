# -*- coding: utf-8 -*-
import os

from PyQt4 import QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'geofollow_dialog_base.ui'))

class GeoFollowDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(GeoFollowDialog, self).__init__(parent)
        self.setupUi(self)

# -*- coding: utf-8 -*-

# Links
# * https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/
# * https://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea/64928#64928

from PyQt4.QtCore import QThread, QObject, pyqtSignal, QSettings
from PyQt4.QtGui import QAction, QIcon
from qgis.core import QgsMessageLog, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPoint, QgsRectangle
from qgis.gui import QgsMessageBar
import json
import socket
import resources
from geofollow_dialog import GeoFollowDialog

class GeoFollow:
    def __init__(self, iface):
        self.iface = iface
        self.connectAction = None
        self.disconnectAction = None
        self.menu = u'GeoFollow'
        self.toolbar = self.iface.addToolBar(u'GeoFollow')
        self.toolbar.setObjectName(u'GeoFollow')
        self.dlg = None
        self.thread = None
        self.worker = None

    def initGui(self):
        self.connectAction = QAction(QIcon(':/plugins/GeoFollow/icon_connect.png'), 'Connect', self.iface.mainWindow())
        self.connectAction.triggered.connect(self.run)
        self.connectAction.setEnabled(True)
        self.connectAction.setStatusTip(u"Connect to GeoFollow server")
        self.toolbar.addAction(self.connectAction)
        self.iface.addPluginToMenu(self.menu, self.connectAction)

        self.disconnectAction = QAction(QIcon(':/plugins/GeoFollow/icon_disconnect.png'), 'Disconnect', self.iface.mainWindow())
        self.disconnectAction.triggered.connect(self.stop)
        self.disconnectAction.setEnabled(False)
        self.disconnectAction.setStatusTip(u"Disconnect from GeoFollow server")
        self.toolbar.addAction(self.disconnectAction)
        self.iface.addPluginToMenu(self.menu, self.disconnectAction)

    def unload(self):
        self.stop()
        self.iface.removePluginMenu(u'GeoFollow', self.connectAction)
        self.iface.removeToolBarIcon(self.connectAction)
        self.iface.removePluginMenu(u'GeoFollow', self.disconnectAction)
        self.iface.removeToolBarIcon(self.disconnectAction)
        del self.toolbar

    def run(self):
        self.dlg = GeoFollowDialog()
        self.dlg.show()
        result = self.dlg.exec_()

        if result:
            self.start(self.dlg.hostLineEdit.text(), self.dlg.portLineEdit.text(), self.dlg.trackerLineEdit.text())
            pass

    def log(self, msg, level=QgsMessageLog.INFO):
        QgsMessageLog.logMessage(msg, 'GeoFollow', level)
        self.iface.mainWindow().statusBar().showMessage("GeoFollow : %s" % msg)

    def error(self, exception):
        if (type(exception) == socket.gaierror) or (type(exception) == socket.error):
            self.iface.messageBar().pushMessage("GeoFollow", str(exception), level=QgsMessageBar.CRITICAL, duration=0)
            QgsMessageLog.logMessage(str(exception), 'GeoFollow', QgsMessageLog.CRITICAL)
            self.stop()
        else:
            self.stop()
            raise exception


    def update(self, data):
        canvas = self.iface.mapCanvas()

        repro = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(data['c']),
            canvas.mapRenderer().destinationCrs()
        )

        pos = data["b"].split(",")
        s_sw = QgsPoint(float(pos[0]), float(pos[1]))
        s_ne = QgsPoint(float(pos[2]), float(pos[3]))

        canvas.setExtent(QgsRectangle(repro.transform(s_sw), repro.transform(s_ne)))
        #cachingEnabled = self.iface.mapCanvas().isCachingEnabled()
        #for layer in self.iface.mapCanvas().layers():
        #    if cachingEnabled:
        #        layer.setCacheImage(None)
        #    layer.triggerRepaint()
        canvas.refresh()
        #self.iface.mapCanvas().refreshAllLayers()
        #qApp.processEvents

    def start(self, host, port, tracker):
        self.connectAction.setEnabled(False)
        self.log("Try to connect to %s:%s/%s" % (host, port, tracker))
        self.thread = QThread()
        self.worker = Worker(host, port, tracker)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.loop)

        self.worker.update.connect(self.update)
        self.worker.status.connect(self.log)
        self.worker.error.connect(self.error)
        self.worker.finished.connect(self.thread.quit)

        self.thread.start()

        self.disconnectAction.setEnabled(True)

    def stop(self):
        self.disconnectAction.setEnabled(False)
        if self.worker:
            self.worker.kill()
        self.log("Stopped !")
        self.connectAction.setEnabled(True)

class Worker(QObject):
    def __init__(self, host, port, tracker, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.host = host
        self.port = port
        self.tracker = tracker

        self.abort = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def loop(self):
        try:
            self.status.emit('Connecting ...')
            self.socket.connect((self.host, int(self.port)))
            self.socket.sendall(self.tracker)
            self.status.emit('Connected !')
            buf = b""
            self.socket.settimeout(10)

            while True:
                if self.abort:
                    break
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    buf = buf + data
                    while True:
                        parts = buf.partition("\n")
                        if parts[1] == '':
                            break

                        buf = parts[2]
                        try:
                            msg = json.loads(parts[0])
                        except ValueError as e:
                            pass
                        else:
                            self.update.emit(msg)
                except socket.timeout as e:
                    pass

            self.status.emit('Disconnected')
        except Exception as e:
            self.error.emit(e)
            self.finished.emit(False)
        else:
            self.finished.emit(True)
        finally:
            self.socket.close()

    def kill(self):
        self.abort = True

    update = pyqtSignal(dict)
    status = pyqtSignal(str)
    error = pyqtSignal(Exception)
    finished = pyqtSignal(bool)
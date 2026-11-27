"""Windows tray, global shortcut and single-instance handling."""
import ctypes
import sys
from ctypes import wintypes
from getpass import getuser
from pathlib import Path
from subprocess import list2cmdline
from threading import Event, Thread
from time import sleep

from PyQt5.QtCore import QObject, QLockFile, QSettings, QStandardPaths, Qt, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon


SHORTCUT = 'Ctrl+Alt+K'
RUN_KEY = r'HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run'
APP_NAME = 'DePocosDownloader'


class GlobalShortcut(QObject):
    activated = pyqtSignal()

    def __init__(self, callback):
        super().__init__()
        self.activated.connect(callback, Qt.QueuedConnection)
        self.registered = False
        self.thread = None
        if sys.platform == 'win32' and QApplication.platformName() == 'windows':
            self.user32 = ctypes.windll.user32
            self.ready = Event()
            self.thread = Thread(target=self.listen, name='Windows keyboard shortcut', daemon=True)
            self.thread.start()
            self.ready.wait()

    def listen(self):
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        message = wintypes.MSG()
        try:
            self.user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
            # MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, virtual key K.
            self.registered = bool(self.user32.RegisterHotKey(None, 1, 0x4003, ord('K')))
        finally:
            self.ready.set()
        if not self.registered:
            return
        try:
            while self.user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == 0x0312 and message.wParam == 1:
                    self.activated.emit()
        finally:
            self.user32.UnregisterHotKey(None, 1)
            self.registered = False

    def unregister(self):
        if self.registered:
            self.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
            self.thread.join(timeout=1)


def startup_command():
    if getattr(sys, 'frozen', False):
        return list2cmdline([sys.executable, '--background'])
    launcher = Path(sys.executable)
    pythonw = launcher.with_name('pythonw.exe')
    return list2cmdline([str(pythonw if pythonw.is_file() else launcher),
                         str(Path(sys.argv[0]).resolve()), '--background'])


def set_startup(enabled):
    settings = QSettings(RUN_KEY, QSettings.NativeFormat)
    if enabled:
        settings.setValue(APP_NAME, startup_command())
    else:
        settings.remove(APP_NAME)
    settings.sync()
    return settings.status() == QSettings.NoError


class Desktop:
    def __init__(self, app, create_window, icon):
        self.app = app
        self.create_window = create_window
        self.window = None
        self.server = QLocalServer(app)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        self.socket_name = f'{APP_NAME}-{getuser()}'
        lock_path = Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation)) / f'{self.socket_name}.lock'
        self.lock = QLockFile(str(lock_path))
        self.lock.setStaleLockTime(0)
        self.icon = icon
        self.tray = None

    def start(self, background):
        if not self.lock.tryLock():
            if not background:
                self.notify_existing()
            return False
        QLocalServer.removeServer(self.socket_name)
        if not self.server.listen(self.socket_name):
            raise RuntimeError('Não foi possível iniciar o canal local do aplicativo.')
        self.server.newConnection.connect(self.accept_connection)
        self.shortcut = GlobalShortcut(self.open_window)
        self.app.aboutToQuit.connect(self.shortcut.unregister)

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.create_tray()
            self.app.setQuitOnLastWindowClosed(False)
        if not background or self.tray is None:
            self.open_window()
        return True

    def notify_existing(self):
        for _ in range(8):
            existing = QLocalSocket()
            existing.connectToServer(self.socket_name)
            if existing.state() == QLocalSocket.ConnectedState or existing.waitForConnected(100):
                existing.write(b'open')
                existing.flush()
                if existing.bytesToWrite():
                    existing.waitForBytesWritten(150)
                existing.disconnectFromServer()
                return
            sleep(.1)

    def accept_connection(self):
        connection = self.server.nextPendingConnection()
        if connection is None:
            return
        connection.disconnected.connect(connection.deleteLater)

        def read():
            if bytes(connection.readAll()) == b'open':
                self.open_window()
            connection.disconnectFromServer()

        connection.readyRead.connect(read)
        if connection.bytesAvailable():
            read()
        elif connection.state() == QLocalSocket.UnconnectedState:
            connection.deleteLater()

    def create_tray(self):
        self.tray = QSystemTrayIcon(self.icon, self.app)
        self.tray.setToolTip('DePoços Downloader' + (f' · {SHORTCUT}' if self.shortcut.registered else ''))
        self.menu = QMenu()
        self.menu.addAction('Abrir DePoços Downloader', self.open_window)
        if sys.platform == 'win32':
            self.startup = self.menu.addAction('Iniciar com o Windows')
            self.startup.setCheckable(True)
            settings = QSettings(RUN_KEY, QSettings.NativeFormat)
            self.startup.setChecked(settings.value(APP_NAME) == startup_command())
            self.startup.triggered.connect(self.toggle_startup)
        self.menu.addSeparator()
        self.menu.addAction('Sair', self.quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def toggle_startup(self, enabled):
        if not set_startup(enabled):
            self.startup.setChecked(not enabled)
            self.tray.showMessage('DePoços Downloader', 'Falha ao alterar a inicialização com o Windows.')

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.open_window()

    def open_window(self):
        if self.window is None:
            self.window = self.create_window(self.tray is not None)
        if self.window.isMinimized():
            self.window.showNormal()
        else:
            self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def quit(self):
        if self.window and self.window.worker:
            self.window.stay_in_tray = False
            self.window.worker.finished.connect(self.app.quit)
            self.window.close()
        else:
            self.app.quit()

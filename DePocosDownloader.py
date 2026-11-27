"""Compact desktop interface for DePoços Downloader."""
import ctypes
import sys
from math import cos, exp, sin, sqrt
from pathlib import Path

from PyQt5.QtCore import (
    QEasingCurve, QEvent, QPoint, QPointF, QRectF, QSettings, QSize, QStandardPaths,
    Qt, QTimer, QUrl,
    QVariantAnimation, pyqtSignal,
)
from PyQt5.QtGui import QColor, QCursor, QDesktopServices, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QLineEdit, QListView, QMainWindow, QPlainTextEdit,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QStyle,
    QStyledItemDelegate, QStyleOptionButton, QStylePainter, QTabBar, QVBoxLayout, QWidget,
)

from downloader import Worker, base_path, validate_url


STYLE = """
QWidget { color: #f8f3fc; font-family: "Segoe UI"; font-size: 14px; }
QFrame#shell {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2c2336, stop:.45 #201a29, stop:1 #19161f);
    border: 1px solid #594763;
    border-radius: 20px;
}
QScrollArea, QWidget#body, QWidget#viewport { background: transparent; border: 0; }
QLabel { background: transparent; }
QLabel#brand { font-size: 17px; font-weight: 700; }
QLabel#section, QLabel#mediaTitle { font-weight: 600; }
QLabel#muted, QLabel#status { color: #c5b7d1; font-size: 13px; }
QLabel#status[tone="error"] { color: #ffb6c1; }
QLabel#status[tone="success"] { color: #b7e7cd; }
QFrame#surface { background: #282132; border: 1px solid #44364f; border-radius: 13px; }
QLineEdit, QComboBox, QPlainTextEdit {
    background: #17131f; border: 1px solid #51415d; border-radius: 9px;
    padding: 7px 10px; selection-background-color: #8054b9;
}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
    border-color: #d9b5ff;
}
QComboBox#quality {
    background: #31253e; border-color: #665073; border-radius: 11px;
    padding: 8px 33px 8px 12px; font-weight: 600;
}
QComboBox#quality:hover { background: #3c2c4c; }
QComboBox#quality:focus, QComboBox#quality:on { border-color: #d2a7f2; }
QComboBox#quality::drop-down { border: 0; width: 30px; }
QComboBox#quality::down-arrow { image: none; }
QListView#qualityMenu {
    background: #271f32; border: 1px solid #685175; border-radius: 10px; padding: 4px;
}
QPlainTextEdit { font-family: Consolas; font-size: 12px; }
QPushButton {
    background: #3a2d48; border: 1px solid #584466; border-radius: 10px;
    padding: 7px 11px; font-weight: 600;
}
QPushButton:hover { background: #49365a; }
QPushButton:pressed { background: #2e2339; }
QPushButton:focus { border-color: #d9b5ff; }
QPushButton:disabled, QLineEdit:disabled, QComboBox:disabled { color: #a294af; }
QPushButton#link, QPushButton#chrome, QPushButton#close {
    background: transparent; border-color: transparent; color: #e0c9f4;
}
QPushButton#link:hover, QPushButton#chrome:hover { background: #49365a; }
QPushButton#link:focus, QPushButton#chrome:focus, QPushButton#close:focus {
    border-color: #d9b5ff;
}
QPushButton#link:disabled { color: #a294af; }
QPushButton#close:hover { background: #5e2e47; color: #fff; }
QPushButton#chrome, QPushButton#close { font-size: 19px; padding: 0; }
QPushButton#primary {
    background: #d8b3ff; border: 1px solid #e4caff; color: #251437;
    font-size: 15px; font-weight: 700;
}
QPushButton#primary:hover { background: #e6ccff; }
QPushButton#primary:pressed { background: #c49aea; }
QPushButton#primary:focus { border: 2px solid #fff3ff; }
QPushButton#primary:disabled { background: #44354e; border-color: #554162; color: #c4b5d1; }
QTabBar::tab { padding: 10px 14px; font-weight: 600; }
QProgressBar { background: #40334d; border: 0; border-radius: 3px; }
QProgressBar::chunk { background: #c998ff; border-radius: 3px; }
QScrollBar:vertical { width: 8px; background: #211a2a; }
QScrollBar::handle:vertical { min-height: 20px; border-radius: 4px; background: #7b628e; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def motion_enabled():
    if QApplication.platformName() != 'windows':
        return False
    enabled = ctypes.c_int(1)
    ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0)
    return bool(enabled.value)


def panel_easing():
    curve = QEasingCurve(QEasingCurve.BezierSpline)
    curve.addCubicBezierSegment(QPointF(.16, 1), QPointF(.3, 1), QPointF(1, 1))
    return curve


SPRING_DURATION_MS = 480
SPRING_DECAY = 22 / 2
SPRING_FREQUENCY = sqrt(260 - SPRING_DECAY ** 2)


def spring_progress(progress):
    # Damped spring with unit mass, stiffness 260 and damping 22.
    if progress >= 1:
        return 1.0
    seconds = progress * SPRING_DURATION_MS / 1000
    angle = SPRING_FREQUENCY * seconds
    return 1 - exp(-SPRING_DECAY * seconds) * (
        cos(angle) + SPRING_DECAY / SPRING_FREQUENCY * sin(angle)
    )


def spring_easing():
    curve = QEasingCurve()
    curve.setCustomType(spring_progress)
    return curve


class PressButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.scale = 1.0
        self.motion = QVariantAnimation(self)
        self.motion.valueChanged.connect(self.update_scale)
        if motion_enabled():
            self.pressed.connect(self.compress)
            self.released.connect(self.rebound)

    def update_scale(self, scale):
        self.scale = scale
        self.update()

    def animate_scale(self, scale, duration, easing):
        self.motion.stop()
        self.motion.setDuration(duration)
        self.motion.setEasingCurve(easing)
        self.motion.setStartValue(self.scale)
        self.motion.setEndValue(scale)
        self.motion.start()

    def compress(self):
        self.animate_scale(.965, 75, QEasingCurve(QEasingCurve.OutQuad))

    def rebound(self):
        # A fast click can release before Qt draws a frame of the press.
        self.update_scale(min(self.scale, .977))
        self.animate_scale(1.0, SPRING_DURATION_MS, spring_easing())

    def paintEvent(self, event):
        if self.scale == 1.0:
            super().paintEvent(event)
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = QRectF(option.rect).center()
        painter.translate(center)
        painter.scale(self.scale, self.scale)
        painter.translate(-center)
        painter.drawControl(QStyle.CE_PushButton, option)


def button(text, action, role=''):
    control = PressButton(text)
    control.setObjectName(role)
    control.setCursor(Qt.PointingHandCursor)
    control.clicked.connect(action)
    return control


class FormatTabs(QTabBar):
    def __init__(self, animated):
        super().__init__()
        self.animated = animated
        self.position = 0.0
        self.selection = QVariantAnimation(self)
        self.selection.setDuration(SPRING_DURATION_MS)
        self.selection.setEasingCurve(spring_easing())
        self.selection.valueChanged.connect(self.move_selection)
        self.currentChanged.connect(self.select_format)

    def move_selection(self, position):
        self.position = position
        self.update()

    def select_format(self, index):
        self.selection.stop()
        if not self.animated or self.count() < 2 or not self.isVisible():
            self.move_selection(float(max(0, index)))
            return
        self.selection.setStartValue(self.position)
        self.selection.setEndValue(float(index))
        self.selection.start()

    def paintEvent(self, event):
        if self.count() < 2:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track = QRectF(self.tabRect(0).united(self.tabRect(1))).adjusted(.5, .5, -.5, -.5)
        painter.setPen(QColor('#4c3c59'))
        painter.setBrush(QColor('#211a2a'))
        painter.drawRoundedRect(track, 13, 13)

        start, end = (QRectF(self.tabRect(index)).adjusted(4, 4, -4, -4) for index in (0, 1))
        position = max(-.01, min(1.01, self.position))
        indicator = QRectF(start)
        indicator.translate((end.left() - start.left()) * position, 0)
        indicator.setWidth(start.width() + (end.width() - start.width()) * position)
        painter.setPen(QColor('#9a70bd' if self.isEnabled() else '#655074'))
        painter.setBrush(QColor('#503969' if self.isEnabled() else '#382c43'))
        painter.drawRoundedRect(indicator, 9, 9)

        font = self.font()
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        selected = self.currentIndex()
        for index in range(self.count()):
            rect = self.tabRect(index)
            text_color = '#fff6ff' if index == selected else '#cfbfdc'
            painter.setPen(QColor(text_color if self.isEnabled() else '#a294af'))
            painter.drawText(rect, Qt.AlignCenter, self.tabText(index))
        if self.hasFocus():
            painter.setPen(QColor('#f1dcff'))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(indicator.adjusted(2, 2, -2, -2), 7, 7)


class QualityItem(QStyledItemDelegate):
    def __init__(self, combo):
        super().__init__(combo)
        self.combo = combo

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width() + 38, max(33, size.height() + 10))

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        row = QRectF(option.rect).adjusted(1, 1, -1, -1)
        chosen = index.row() == self.combo.currentIndex()
        if option.state & (QStyle.State_Selected | QStyle.State_MouseOver):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#503967'))
            painter.drawRoundedRect(row, 7, 7)
        elif chosen:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#382a49'))
            painter.drawRoundedRect(row, 7, 7)
        painter.setPen(QColor('#f8f3fc'))
        painter.drawText(row.adjusted(10, 0, -30, 0), Qt.AlignVCenter | Qt.AlignLeft,
                         str(index.data()))
        if chosen:
            x, y = row.right() - 13, row.center().y()
            painter.setPen(QPen(QColor('#e5c4ff'), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(QPointF(x - 5, y), QPointF(x - 2, y + 3))
            painter.drawLine(QPointF(x - 2, y + 3), QPointF(x + 4, y - 3))
        painter.restore()


class QualitySelector(QComboBox):
    def __init__(self, animated):
        super().__init__()
        self.animated = animated
        self.setObjectName('quality')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(200)
        self.setMaxVisibleItems(7)

        menu = QListView()
        menu.setObjectName('qualityMenu')
        menu.setMouseTracking(True)
        menu.setUniformItemSizes(True)
        menu.setItemDelegate(QualityItem(self))
        self.setView(menu)

        self.reveal_amount = 0.0
        self.motion = QVariantAnimation(self)
        self.motion.setEasingCurve(panel_easing())
        self.motion.valueChanged.connect(self.draw_reveal)
        self.menu_opacity = QGraphicsOpacityEffect(menu)
        self.menu_opacity.setOpacity(1)
        if animated:
            menu.setGraphicsEffect(self.menu_opacity)
        menu.installEventFilter(self)

    def animate_reveal(self, target):
        self.motion.stop()
        if not self.animated:
            self.draw_reveal(target)
            return
        self.motion.setDuration(220 if target else 150)
        self.motion.setStartValue(self.reveal_amount)
        self.motion.setEndValue(target)
        self.motion.start()

    def showPopup(self):
        if self.animated:
            self.menu_opacity.setOpacity(.25)
        super().showPopup()
        self.animate_reveal(1.0)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Hide and watched is self.view():
            self.animate_reveal(0.0)
        return super().eventFilter(watched, event)

    def draw_reveal(self, progress):
        self.reveal_amount = progress
        self.menu_opacity.setOpacity(.25 + .75 * progress)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() - 16, self.height() / 2)
        painter.rotate(180 * self.reveal_amount)
        color = QColor('#d9b5ff' if self.isEnabled() else '#a294af')
        painter.setPen(QPen(color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(-4, -2), QPointF(0, 2))
        painter.drawLine(QPointF(0, 2), QPointF(4, -2))


class Disclosure(QWidget):
    """Clip the content as it expands and reverse from the current height."""
    height_changed = pyqtSignal()

    def __init__(self, content, animated):
        super().__init__()
        self.content = content
        content.setParent(self)
        self.effect = QGraphicsOpacityEffect(content)
        self.effect.setOpacity(1)
        content.setGraphicsEffect(self.effect)
        self.animation = QVariantAnimation(self)
        self.animation.valueChanged.connect(self.set_extent)
        self.animation.finished.connect(self.finish)
        self.animated = animated
        self.opened = False
        self.setFixedHeight(0)
        content.hide()
        self.hide()
        content.installEventFilter(self)

    def reveal(self, opened):
        if opened == self.opened:
            return
        self.opened = opened
        self.animation.stop()
        if opened:
            self.show()
            self.content.show()
            self.content.resize(self.width(), self.content_height())
        target = self.content.height() if opened else 0
        self.content.setEnabled(opened)
        self.animate_to(target)

    def content_height(self):
        hint = self.content.sizeHint().height()
        return max(self.content.minimumHeight(), min(hint, self.content.maximumHeight()))

    def animate_to(self, target):
        self.animation.stop()
        if self.animated and self.height() != target:
            self.animation.setDuration(300 if self.opened else 120)
            self.animation.setEasingCurve(panel_easing() if self.opened else QEasingCurve(QEasingCurve.InQuad))
            self.animation.setStartValue(self.height())
            self.animation.setEndValue(target)
            self.animation.start()
        else:
            self.set_extent(target)
            self.finish()

    def set_extent(self, height):
        self.setFixedHeight(height)
        self.effect.setOpacity(min(1, height / max(1, self.content.height())))
        self.height_changed.emit()

    def finish(self):
        if not self.opened:
            self.hide()
            self.content.hide()
        self.height_changed.emit()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.LayoutRequest and self.opened:
            height = self.content_height()
            if height != self.content.height():
                self.content.resize(self.width(), height)
                self.animate_to(height)
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        self.content.resize(event.size().width(), self.content.height())
        super().resizeEvent(event)


class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.closing = False
        self.result_folder = None
        self.first_show = True
        self.opening_offset = 10
        self.animated = motion_enabled()
        self.settings = QSettings('GabrielDePocos', 'DePocosDownloader')
        self.setWindowTitle('DePoços Downloader')
        icon = QIcon(str(base_path() / 'icone.ico'))
        self.setWindowIcon(icon)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.window_motion = QVariantAnimation(self)

        shell = QFrame()
        shell.setObjectName('shell')
        self.setCentralWidget(shell)
        frame = QVBoxLayout(shell)
        frame.setContentsMargins(1, 1, 1, 1)
        frame.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(60)
        header.mousePressEvent = self.drag_window
        bar = QHBoxLayout(header)
        bar.setContentsMargins(20, 0, 14, 0)
        bar.setSpacing(8)
        mark = QLabel()
        mark.setPixmap(icon.pixmap(QSize(26, 26)))
        title = QLabel('DePoços Downloader')
        title.setObjectName('brand')
        bar.addWidget(mark)
        bar.addWidget(title, 1)
        for text, name, role, action in (
            ('−', 'Minimizar', 'chrome', self.showMinimized),
            ('×', 'Fechar', 'close', self.request_close),
        ):
            control = button(text, action, role)
            control.setFixedSize(32, 32)
            control.setToolTip(name)
            control.setAccessibleName(name)
            bar.addWidget(control)
        frame.addWidget(header)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setObjectName('viewport')
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.body.setObjectName('body')
        scroll.setWidget(self.body)
        frame.addWidget(scroll)
        self.form = QVBoxLayout(self.body)
        self.form.setContentsMargins(20, 0, 20, 19)
        self.form.setSpacing(10)
        self.build_form()
        self.body.installEventFilter(self)
        bounds = self.available_screen()
        self.setFixedWidth(min(464, bounds.width() - 32))
        self.fit_window()

    def build_form(self):
        link_header = QHBoxLayout()
        label = QLabel('Link do vídeo')
        label.setObjectName('section')
        link_header.addWidget(label, 1)
        self.preview_btn = button('Ver detalhes', self.preview, 'link')
        self.preview_btn.setEnabled(False)
        link_header.addWidget(self.preview_btn)
        self.form.addLayout(link_header)

        link_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setAccessibleName('Link do vídeo')
        self.url_input.setPlaceholderText('Cole aqui o link do vídeo')
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setFixedHeight(42)
        self.url_input.textChanged.connect(self.reset_activity)
        self.paste_btn = button('Colar', self.paste_link)
        self.paste_btn.setFixedHeight(42)
        link_row.addWidget(self.url_input, 1)
        link_row.addWidget(self.paste_btn)
        self.form.addLayout(link_row)

        self.kind = FormatTabs(self.animated)
        self.kind.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.kind.setAccessibleName('Formato do download')
        self.kind.addTab('Vídeo')
        self.kind.addTab('Áudio MP3')
        self.kind.setTabToolTip(1, 'MP3 a 192 kbps')
        self.form.addWidget(self.kind)
        self.kind.currentChanged.connect(self.update_quality)

        options_row = QHBoxLayout()
        self.destination = QLabel()
        self.destination.setObjectName('muted')
        self.destination.setTextFormat(Qt.PlainText)
        self.destination.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        options_row.addWidget(self.destination, 1)
        self.options_btn = button('Opções ▾', self.toggle_options, 'link')
        self.options_btn.setCheckable(True)
        options_row.addWidget(self.options_btn)
        self.form.addLayout(options_row)
        self.options = self.make_options()

        self.download_btn = button('Baixar vídeo', self.download, 'primary')
        self.url_input.returnPressed.connect(self.download_btn.click)
        self.download_btn.setFixedHeight(44)
        self.form.addWidget(self.download_btn)
        self.activity = self.make_activity()
        self.diagnostics = Disclosure(self.log, self.animated)
        self.diagnostics.height_changed.connect(self.fit_window)
        self.form.addWidget(self.diagnostics)

    def surface(self):
        panel = QFrame()
        panel.setObjectName('surface')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)
        return panel, layout

    def add_disclosure(self, content):
        panel = Disclosure(content, self.animated)
        panel.height_changed.connect(self.fit_window)
        self.form.addWidget(panel)
        return panel

    def make_options(self):
        panel, layout = self.surface()
        self.quality = QualitySelector(self.animated)
        self.quality.setAccessibleName('Qualidade máxima do vídeo')
        for label, height in (
            ('Melhor disponível', None), ('4K · 2160p', 2160), ('2K · 1440p', 1440),
            ('Full HD · 1080p', 1080), ('HD · 720p', 720), ('480p', 480), ('360p', 360),
        ):
            self.quality.addItem(label, height)
        self.quality.setCurrentIndex(3)
        self.quality_group = QWidget()
        quality_row = QHBoxLayout(self.quality_group)
        quality_row.setContentsMargins(0, 0, 0, 0)
        quality_row.addWidget(QLabel('Qualidade máxima'), 1)
        quality_row.addWidget(self.quality)
        layout.addWidget(self.quality_group)
        layout.addWidget(QLabel('Pasta de destino'))
        default = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.folder = QLineEdit(str(self.settings.value('folder', default or str(Path.home() / 'Downloads'))))
        self.folder.setAccessibleName('Pasta de destino')
        self.folder.textChanged.connect(self.update_destination)
        self.folder_btn = button('Escolher…', self.choose_folder)
        self.folder_btn.setAccessibleName('Escolher pasta de destino')
        self.open_btn = button('Abrir pasta', lambda: self.open_folder())
        row = QHBoxLayout()
        row.addWidget(self.folder, 1)
        row.addWidget(self.folder_btn)
        row.addWidget(self.open_btn)
        layout.addLayout(row)
        self.update_destination()
        return self.add_disclosure(panel)

    def make_activity(self):
        panel, layout = self.surface()
        self.media_title = QLabel()
        self.media_title.setObjectName('mediaTitle')
        self.media_detail = QLabel()
        self.media_detail.setObjectName('muted')
        self.status = QLabel()
        self.status.setObjectName('status')
        for label in (self.media_title, self.media_detail, self.status):
            label.setTextFormat(Qt.PlainText)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            layout.addWidget(label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setAccessibleName('Progresso do download')
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)
        row = QHBoxLayout()
        self.cancel_btn = button('Cancelar', self.cancel)
        self.result_folder_btn = button('Abrir pasta', lambda: self.open_folder(self.result_folder))
        self.details_btn = button('Diagnóstico ▾', self.toggle_diagnostics, 'link')
        self.details_btn.setCheckable(True)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.result_folder_btn)
        row.addStretch()
        row.addWidget(self.details_btn)
        layout.addLayout(row)
        self.log = QPlainTextEdit()
        self.log.setAccessibleName('Diagnóstico da operação')
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(150)
        self.log.setFixedHeight(96)
        return self.add_disclosure(panel)

    def available_screen(self):
        screen = self.windowHandle().screen() if self.isVisible() and self.windowHandle() else (
            QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        )
        return screen.availableGeometry()

    def fit_window(self):
        bounds = self.available_screen()
        self.body.layout().activate()
        self.setFixedHeight(min(self.body.sizeHint().height() + 64, bounds.height() - 32))
        if self.isVisible() and self.y() + self.height() > bounds.bottom() + 1:
            self.move(self.x(), bounds.bottom() - self.height() + 1)
        self.update_destination()

    def eventFilter(self, watched, event):
        if watched is self.body and event.type() == QEvent.LayoutRequest:
            QTimer.singleShot(0, self.fit_window)
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.first_show:
            return
        self.first_show = False
        bounds = self.available_screen()
        end = QPoint(bounds.right() - self.width() - 19, bounds.top() + 20)
        self.move(end)
        self.update_destination()
        self.url_input.setFocus()
        if self.animated:
            self.setWindowOpacity(0)
            self.move(end + QPoint(0, 10))
            self.window_motion.setDuration(300)
            self.window_motion.setEasingCurve(panel_easing())
            self.window_motion.setStartValue(0.0)
            self.window_motion.setEndValue(1.0)
            self.window_motion.valueChanged.connect(self.animate_opening)
            self.window_motion.start()

    def animate_opening(self, opacity):
        self.setWindowOpacity(opacity)
        # Apply only the change in offset so dragging never resets the position.
        offset = round(10 * (1 - opacity))
        self.move(self.pos() + QPoint(0, offset - self.opening_offset))
        self.opening_offset = offset

    def drag_window(self, event):
        if event.button() == Qt.LeftButton and self.windowHandle():
            self.windowHandle().startSystemMove()

    def request_close(self):
        if self.worker or not self.animated:
            self.close()
            return
        if self.closing:
            return
        self.closing = True
        self.window_motion.stop()
        self.window_motion.valueChanged.disconnect(self.animate_opening)
        self.window_motion.setDuration(120)
        self.window_motion.setEasingCurve(QEasingCurve.InQuad)
        self.window_motion.setStartValue(self.windowOpacity())
        self.window_motion.setEndValue(0.0)
        self.window_motion.valueChanged.connect(self.setWindowOpacity)
        self.window_motion.finished.connect(self.close)
        self.window_motion.start()

    def toggle_options(self, opened):
        self.options_btn.setChecked(opened)
        self.options_btn.setText('Opções ▴' if opened else 'Opções ▾')
        self.options.reveal(opened)

    def toggle_diagnostics(self, opened):
        self.details_btn.setChecked(opened)
        self.details_btn.setText('Diagnóstico ▴' if opened else 'Diagnóstico ▾')
        self.diagnostics.reveal(opened)

    def update_destination(self):
        path = self.folder.text().strip()
        folder_name = (Path(path).name or path) if path else 'nenhuma pasta escolhida'
        text = f'Salvar em {folder_name}'
        width = self.destination.width() if self.isVisible() else 280
        self.destination.setText(self.destination.fontMetrics().elidedText(text, Qt.ElideMiddle, width))
        self.destination.setToolTip(path)
        self.destination.setAccessibleName(f'Salvar em {path or folder_name}')

    def paste_link(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)
            self.url_input.setFocus()
        else:
            self.show_error('A área de transferência está vazia.')

    def reset_activity(self, text):
        if self.worker is None:
            self.preview_btn.setEnabled(bool(text.strip()))
            self.toggle_diagnostics(False)
            self.activity.reveal(False)

    def update_quality(self):
        audio = self.kind.currentIndex() == 1
        self.quality_group.setVisible(not audio)
        self.quality.setEnabled(self.worker is None and not audio)
        self.download_btn.setText('Baixar MP3' if audio else 'Baixar vídeo')

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Salvar downloads em', self.folder.text())
        if path:
            self.folder.setText(path)

    def open_folder(self, folder=None):
        folder = folder if folder is not None else self.folder.text().strip()
        path = Path(folder).expanduser()
        if folder and path.is_dir() and QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve()))):
            return
        self.show_error('Não foi possível abrir a pasta. Confira o destino em Opções.')

    def preview(self):
        self.start(False)

    def download(self):
        self.start(True)

    def start(self, downloading):
        if self.worker is not None or self.closing:
            return
        try:
            url = validate_url(self.url_input.text())
        except ValueError:
            self.show_error('Use um link com https://.')
            self.url_input.setFocus()
            return
        folder = self.folder.text().strip()
        if downloading and not folder:
            self.show_error('Escolha uma pasta de destino.')
            self.toggle_options(True)
            self.folder.setFocus()
            return
        self.toggle_diagnostics(False)
        self.log.clear()
        self.set_activity('Buscando informações…', downloading=downloading)
        self.worker = Worker(url, folder if downloading else None, self.quality.currentData(),
                             self.kind.currentIndex() == 1, self)
        self.worker.status.connect(self.on_status)
        self.worker.progress.connect(self.on_progress)
        self.worker.metadata.connect(self.on_metadata)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(self.on_finished)
        self.set_busy(True)
        self.on_progress(-1)
        self.progress_bar.show()
        self.activity.reveal(True)
        self.cancel_btn.setFocus(Qt.OtherFocusReason)
        self.worker.start()

    def set_activity(self, title, downloading=False):
        self.set_line(self.media_title, title)
        self.set_line(self.media_detail, '')
        self.set_status('Preparando download…' if downloading else '')
        self.result_folder_btn.hide()
        self.details_btn.hide()
        self.cancel_btn.hide()
        self.progress_bar.hide()

    def show_error(self, message):
        self.toggle_diagnostics(False)
        self.set_activity('Confira antes de continuar')
        self.set_status(message, 'error')
        self.activity.reveal(True)

    def set_busy(self, busy):
        for control in (self.url_input, self.paste_btn, self.kind, self.folder,
                        self.folder_btn, self.open_btn, self.download_btn):
            control.setEnabled(not busy)
        self.preview_btn.setEnabled(not busy and bool(self.url_input.text().strip()))
        self.cancel_btn.setEnabled(busy)
        self.cancel_btn.setVisible(busy)
        self.update_quality()

    def set_line(self, label, text):
        text = ' '.join(text.split())
        width = max(180, self.width() - 70)
        label.setText(label.fontMetrics().elidedText(text, Qt.ElideRight, width))
        label.setToolTip(text)
        label.setAccessibleName(text)
        label.setVisible(bool(text))

    def set_status(self, message, tone=''):
        if self.status.property('tone') != tone:
            self.status.setProperty('tone', tone)
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)
        self.set_line(self.status, message)

    def on_status(self, message):
        if not message.startswith('Baixando arquivo'):
            self.log.appendPlainText(message)
        if self.worker.cancel_event.is_set() or message.startswith(('Aviso:', 'Diagnóstico')):
            return
        self.set_status(message)

    def on_progress(self, value):
        if self.worker.cancel_event.is_set():
            return
        self.progress_bar.setRange(0, 0 if value < 0 and self.animated else 100)
        if value >= 0 or not self.animated:
            self.progress_bar.setValue(max(0, value))

    def on_metadata(self, data):
        self.set_line(self.media_title, data.get('title') or 'Sem título')
        duration = data.get('duration')
        if duration is None:
            time = 'Duração não informada'
        else:
            minutes, seconds = divmod(int(duration), 60)
            hours, minutes = divmod(minutes, 60)
            time = f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes}:{seconds:02d}'
        self.set_line(self.media_detail, f"{data.get('uploader') or 'Autor não informado'} · {time}")

    def on_result(self, success, message):
        downloaded = success and bool(self.worker.folder)
        cancelled = self.worker.cancel_event.is_set() and not success
        self.log.appendPlainText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if downloaded else 0)
        self.progress_bar.setVisible(downloaded)
        self.cancel_btn.hide()
        self.result_folder_btn.setVisible(downloaded)
        self.details_btn.setVisible(not cancelled)
        if success:
            self.set_status('Download concluído' if downloaded else '', 'success')
            if downloaded:
                self.result_folder = self.worker.folder
                self.settings.setValue('folder', self.worker.folder)
        else:
            self.set_line(self.media_title, 'Operação cancelada' if cancelled else 'Não foi possível concluir')
            self.set_line(self.media_detail, '')
            self.set_status('Tente novamente ou abra o diagnóstico.' if not cancelled else '',
                            '' if cancelled else 'error')

    def on_finished(self):
        previous_action = self.download_btn if self.worker.folder else self.preview_btn
        self.worker.deleteLater()
        self.worker = None
        self.set_busy(False)
        if self.closing:
            self.close()
        else:
            previous_action.setFocus(Qt.OtherFocusReason)

    def cancel(self):
        if self.worker:
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.progress_bar.setRange(0, 100)
            self.set_status('Cancelando… A etapa em andamento precisa terminar.')

    def closeEvent(self, event):
        if self.worker:
            self.closing = True
            self.cancel()
            event.ignore()
        else:
            self.window_motion.stop()
            event.accept()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

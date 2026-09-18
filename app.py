import sys
import hashlib
from datetime import datetime, timedelta

from PySide6.QtCore import (
    Qt, Signal, Slot, QThread, QObject, QTimer, QSize, QPoint,
    QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QColor, QAction
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QDialog,
    QStackedWidget,
    QFrame,
    QMenu,
)

import storage
import chat_engine

ICON_FONT = "Segoe UI Symbol"

THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "sidebar_bg": "#F6F6F8",
        "border": "#E3E3E8",
        "text": "#1C1C1E",
        "title": "#111111",
        "muted": "#8E8E93",
        "faint": "#A6A6AC",
        "scrollbar": "#C7C7CC",
        "bubble_other": "#E9E9EB",
        "bubble_other_hover": "#E0E0E4",
        "bubble_user": "#0A84FF",
        "bubble_user_hover": "#0A79ED",
        "accent_pressed": "#0866C3",
        "input_bg": "#F6F6F8",
        "input_bg_focus": "#FFFFFF",
        "input_bg_disabled": "#EBEBEE",
        "search_bg": "#E9E9EC",
        "selected_row": "#E5E5EA",
        "card_bg": "#FFFFFF",
        "cancel_bg": "#E9E9EB",
        "cancel_hover": "#DDDDE0",
        "error_bg": "#FFE5E4",
        "error_text": "#BF3B34",
        "create_disabled": "#A6C9F0",
    },
    "dark": {
        "bg": "#1C1C1E",
        "sidebar_bg": "#131315",
        "border": "#2C2C2E",
        "text": "#F5F5F7",
        "title": "#FFFFFF",
        "muted": "#98989D",
        "faint": "#6E6E73",
        "scrollbar": "#48484A",
        "bubble_other": "#26262A",
        "bubble_other_hover": "#34343A",
        "bubble_user": "#0A84FF",
        "bubble_user_hover": "#0A74E0",
        "accent_pressed": "#0857D9",
        "input_bg": "#26262A",
        "input_bg_focus": "#26262A",
        "input_bg_disabled": "#1F1F21",
        "search_bg": "#26262A",
        "selected_row": "#3A3A3C",
        "card_bg": "#1E1E20",
        "cancel_bg": "#2A2A2C",
        "cancel_hover": "#3A3A3C",
        "error_bg": "#442424",
        "error_text": "#FF9C8F",
        "create_disabled": "#3B5C86",
    },
}


def build_metrics(scale=1.0):
    return {
        "scale": scale,
        "sidebar_w": max(240, int(300 * scale)),
        "row_h": max(48, int(64 * scale)),
        "avatar": max(28, int(40 * scale)),
        "preview_w": max(110, int(148 * scale)),
        "add_btn": max(24, int(30 * scale)),
        "send_btn": max(28, int(36 * scale)),
        "sidebar_header_h": max(72, int(96 * scale)),
        "chat_header_h": max(44, int(56 * scale)),
        "card_w": max(300, int(400 * scale)),
        "card_h": max(200, int(252 * scale)),
        "settings_card_w": max(330, int(400 * scale)),
        "settings_card_h": max(300, int(360 * scale)),
        "font_avatar": max(13, int(18 * scale)),
        "font_icon_add": max(13, int(18 * scale)),
        "font_icon_send": max(12, int(16 * scale)),
    }


def build_stylesheet(theme, scale=1.0):
    pal = dict(THEMES.get(theme, THEMES["light"]))
    px = lambda v: f"{max(1, round(v * scale))}px"
    S = {
        "fs": px(14),
        "fs_title": px(23),
        "fs_count": px(12),
        "fs_search": px(13),
        "fs_chat_title": px(16),
        "fs_subtitle": px(11),
        "fs_composer": px(15),
        "fs_placeholder_title": px(18),
        "fs_placeholder_hint": px(13),
        "fs_bubble": px(15),
        "fs_time": px(10),
        "fs_typing": px(15),
        "fs_contact_name": px(15),
        "fs_preview": px(12),
        "fs_contact_time": px(11),
        "fs_popup_title": px(17),
        "fs_popup_subtitle": px(13),
        "fs_popup_input": px(15),
        "fs_popup_btn": px(15),
        "fs_menu": px(13),
        "pad_search": f"{px(6)} {px(12)}",
        "pad_composer": f"{px(9)} {px(16)}",
        "pad_bubble": f"{px(10)} {px(14)}",
        "pad_popup_input": f"{px(10)} {px(14)}",
        "pad_popup_btn": f"{px(11)} 0",
        "pad_menu": f"{px(7)} {px(22)}",
        "r_bubble": px(18),
        "r_tail": px(5),
        "r_search": px(10),
        "r_composer": px(18),
        "r_add": px(15),
        "r_send": px(18),
        "r_option": px(12),
        "r_input": px(12),
        "r_card": px(20),
        "r_menu": px(5),
        "border1": "1px",
    }
    qss = _TEMPLATE
    for k, v in S.items():
        qss = qss.replace(f"@@{k}@@", v)
    for k, v in pal.items():
        qss = qss.replace(f"@@{k}@@", v)
    return qss


_TEMPLATE = """
QWidget {
    font-family: "Segoe UI";
    font-size: @@fs@@;
    color: @@text@@;
}
QMainWindow, #RootContainer {
    background-color: @@bg@@;
}
#Sidebar {
    background-color: @@sidebar_bg@@;
    border-right: @@border1@@ solid @@border@@;
}
#SidebarHeader {
    background-color: @@sidebar_bg@@;
    border-bottom: @@border1@@ solid @@border@@;
}
#SidebarTitle {
    font-size: @@fs_title@@;
    font-weight: 700;
    color: @@title@@;
}
#SidebarCount {
    font-size: @@fs_count@@;
    color: @@muted@@;
}
#SearchInput {
    border: none;
    background-color: @@search_bg@@;
    border-radius: @@r_search@@;
    padding: @@pad_search@@;
    font-size: @@fs_search@@;
    color: @@text@@;
}
#SearchInput:focus {
    background-color: @@input_bg_focus@@;
    border: @@border1@@ solid @@bubble_user@@;
}
#SidebarList {
    background-color: @@sidebar_bg@@;
    border: none;
    outline: none;
}
#SidebarList::item {
    border: none;
}
#AddContactButton, #SettingsButton {
    background-color: @@bubble_user@@;
    color: #FFFFFF;
    border: none;
    border-radius: @@r_add@@;
}
#SettingsButton {
    background-color: transparent;
    color: @@bubble_user@@;
    border: @@border1@@ solid @@bubble_user@@;
}
#SettingsButton:hover {
    background-color: @@search_bg@@;
}
#AddContactButton:hover {
    background-color: @@bubble_user_hover@@;
}
#AddContactButton:pressed {
    background-color: @@accent_pressed@@;
}
#ChatHeader {
    background-color: @@bg@@;
    border-bottom: @@border1@@ solid @@border@@;
}
#ChatTitle {
    font-size: @@fs_chat_title@@;
    font-weight: 600;
}
#ChatSubtitle {
    font-size: @@fs_subtitle@@;
    color: @@muted@@;
}
#MessageScroll {
    border: none;
    background-color: @@bg@@;
}
#ChatBackground {
    background-color: @@bg@@;
}
#ComposerContainer {
    background-color: @@bg@@;
    border-top: @@border1@@ solid @@border@@;
}
#ComposerInput {
    border: @@border1@@ solid @@border@@;
    background-color: @@input_bg@@;
    border-radius: @@r_composer@@;
    padding: @@pad_composer@@;
    font-size: @@fs_composer@@;
    color: @@text@@;
}
#ComposerInput:focus {
    border: @@border1@@ solid @@bubble_user@@;
    background-color: @@input_bg_focus@@;
}
#ComposerInput:disabled {
    background-color: @@input_bg_disabled@@;
    color: @@faint@@;
}
#SendButton {
    background-color: @@bubble_user@@;
    color: #FFFFFF;
    border: none;
    border-radius: @@r_send@@;
}
#SendButton:hover {
    background-color: @@bubble_user_hover@@;
}
#SendButton:pressed {
    background-color: @@accent_pressed@@;
}
#SendButton:disabled {
    background-color: @@input_bg_disabled@@;
}
#PlaceholderTitle {
    font-size: @@fs_placeholder_title@@;
    font-weight: 600;
    color: @@muted@@;
}
#PlaceholderHint {
    font-size: @@fs_placeholder_hint@@;
    color: @@faint@@;
}
QLabel#BubbleUser {
    background-color: @@bubble_user@@;
    color: #FFFFFF;
    border-top-left-radius: @@r_bubble@@;
    border-top-right-radius: @@r_bubble@@;
    border-bottom-left-radius: @@r_bubble@@;
    border-bottom-right-radius: @@r_tail@@;
    padding: @@pad_bubble@@;
    font-size: @@fs_bubble@@;
}
QLabel#BubbleUser:hover {
    background-color: @@bubble_user_hover@@;
}
QLabel#BubbleOther {
    background-color: @@bubble_other@@;
    color: @@text@@;
    border-top-left-radius: @@r_bubble@@;
    border-top-right-radius: @@r_bubble@@;
    border-bottom-left-radius: @@r_tail@@;
    border-bottom-right-radius: @@r_bubble@@;
    padding: @@pad_bubble@@;
    font-size: @@fs_bubble@@;
}
QLabel#BubbleOther:hover {
    background-color: @@bubble_other_hover@@;
}
QLabel#BubbleError {
    background-color: @@error_bg@@;
    color: @@error_text@@;
    border-top-left-radius: @@r_bubble@@;
    border-top-right-radius: @@r_bubble@@;
    border-bottom-left-radius: @@r_tail@@;
    border-bottom-right-radius: @@r_bubble@@;
    padding: @@pad_bubble@@;
    font-size: @@fs_bubble@@;
}
#BubbleTime {
    font-size: @@fs_time@@;
    color: @@faint@@;
}
#TypingDots {
    font-size: @@fs_typing@@;
    color: @@text@@;
}
#ContactName {
    font-size: @@fs_contact_name@@;
    font-weight: 600;
}
#ContactPreview {
    font-size: @@fs_preview@@;
    color: @@muted@@;
}
#ContactTime {
    font-size: @@fs_contact_time@@;
    color: @@faint@@;
}
#PopupCard {
    background-color: @@card_bg@@;
    border-radius: @@r_card@@;
}
#PopupTitle {
    font-size: @@fs_popup_title@@;
    font-weight: 600;
    color: @@title@@;
}
#PopupSubtitle {
    font-size: @@fs_popup_subtitle@@;
    color: @@muted@@;
}
#PopupSection {
    font-size: @@fs_count@@;
    font-weight: 600;
    color: @@muted@@;
}
#PopupInput {
    border: @@border1@@ solid @@border@@;
    background-color: @@input_bg@@;
    border-radius: @@r_input@@;
    padding: @@pad_popup_input@@;
    font-size: @@fs_popup_input@@;
    color: @@text@@;
}
#PopupInput:focus {
    border: @@border1@@ solid @@bubble_user@@;
    background-color: @@input_bg_focus@@;
}
#PopupCreate {
    background-color: @@bubble_user@@;
    color: #FFFFFF;
    border: none;
    border-radius: @@r_input@@;
    font-size: @@fs_popup_btn@@;
    font-weight: 600;
    padding: @@pad_popup_btn@@;
}
#PopupCreate:hover {
    background-color: @@bubble_user_hover@@;
}
#PopupCreate:disabled {
    background-color: @@create_disabled@@;
}
#PopupCancel {
    background-color: @@cancel_bg@@;
    color: @@text@@;
    border: none;
    border-radius: @@r_input@@;
    font-size: @@fs_popup_btn@@;
    font-weight: 600;
    padding: @@pad_popup_btn@@;
}
#PopupCancel:hover {
    background-color: @@cancel_hover@@;
}
#OptionButton {
    background-color: @@search_bg@@;
    color: @@text@@;
    border: none;
    border-radius: @@r_option@@;
    font-size: @@fs_popup_btn@@;
    padding: @@pad_popup_btn@@;
}
#OptionButton:hover {
    background-color: @@bubble_other_hover@@;
}
#OptionButton[active="true"] {
    background-color: @@bubble_user@@;
    color: #FFFFFF;
}
#OptionButton[active="true"]:hover {
    background-color: @@bubble_user_hover@@;
}
QMenu {
    background-color: @@card_bg@@;
    border: @@border1@@ solid @@border@@;
    padding: @@pad_menu@@;
}
QMenu::item {
    padding: @@pad_menu@@;
    border-radius: @@r_menu@@;
    font-size: @@fs_menu@@;
    color: @@text@@;
}
QMenu::item:selected {
    background-color: @@bubble_user@@;
    color: #FFFFFF;
}
QMenu::separator {
    height: @@border1@@;
    background: @@border@@;
    margin: @@border1@@ 4px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: @@scrollbar@@;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""


def format_relative_time(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return str(value)
    today = datetime.now().date()
    if dt.date() == today:
        return dt.strftime("%H:%M")
    if dt.date() == today - timedelta(days=1):
        return "Yesterday"
    if dt.year == today.year:
        return dt.strftime("%b %d")
    return dt.strftime("%b %d, %Y")


def format_bubble_time(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except ValueError:
        return str(value)


def _repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class ChatWorker(QObject):
    reply_ready = Signal(str, str)
    request_failed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._queue = []

    @Slot(str, str, object)
    def enqueue(self, contact_id, personality, history):
        self._queue.append((contact_id, personality, [dict(m) for m in history]))
        while self._queue:
            cid, name, history = self._queue.pop(0)
            try:
                reply = chat_engine.chat(name, history)
            except Exception as e:
                self.request_failed.emit(cid, str(e))
            else:
                self.reply_ready.emit(cid, reply)


class PopupShell(QDialog):
    """Frameless card popup over a dimmed backdrop."""

    def __init__(self, parent=None, card_w=400, card_h=260):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self._card_w = card_w
        self._card_h = card_h
        self.card = QFrame(self)
        self.card.setObjectName("PopupCard")
        self.card.setFixedSize(card_w, card_h)

    def showEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            origin = parent.mapToGlobal(QPoint(0, 0))
            self.setGeometry(origin.x(), origin.y(), parent.width(), parent.height())
        super().showEvent(event)
        self._fade_in()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        x = (self.width() - self.card.width()) // 2
        y = (self.height() - self.card.height()) // 2 - 30
        self.card.move(max(0, x), max(0, y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))
        painter.end()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if not self.card.geometry().contains(pos):
            self.reject()
        else:
            super().mousePressEvent(event)

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(180)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()


class ContactPopup(PopupShell):
    def __init__(self, parent=None):
        m = build_metrics()
        if parent is not None and hasattr(parent, "m"):
            m = parent.m
        super().__init__(parent, card_w=m["card_w"], card_h=m["card_h"])

        title = QLabel("New Contact")
        title.setObjectName("PopupTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Just a name — it becomes the AI's personality.")
        subtitle.setObjectName("PopupSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("PopupInput")
        self.name_edit.setPlaceholderText("Name / personality")

        self.create_button = QPushButton("Create")
        self.create_button.setObjectName("PopupCreate")
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("PopupCancel")

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(cancel_button, 1)
        buttons.addWidget(self.create_button, 1)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(22, 22, 22, 20)
        card_layout.setSpacing(10)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.name_edit)
        card_layout.addStretch(1)
        card_layout.addLayout(buttons)

        self.create_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.name_edit.textChanged.connect(self._validate)
        self.name_edit.returnPressed.connect(self._confirm_maybe)
        self._validate()

    def _validate(self):
        self.create_button.setEnabled(bool(self.name_edit.text().strip()))

    def _confirm_maybe(self):
        if self.name_edit.text().strip():
            self.accept()

    def name(self):
        return self.name_edit.text().strip()

    def showEvent(self, event):
        super().showEvent(event)
        self.name_edit.setFocus()


class SettingsPopup(PopupShell):
    def __init__(self, parent=None):
        m = build_metrics()
        if parent is not None and hasattr(parent, "m"):
            m = parent.m
        super().__init__(parent, card_w=m["settings_card_w"], card_h=m["settings_card_h"])

        self.window_owner = parent
        self.settings = dict(parent.settings) if parent is not None else dict(storage.DEFAULT_SETTINGS)

        title = QLabel("Settings")
        title.setObjectName("PopupTitle")
        title.setAlignment(Qt.AlignCenter)

        theme_label = QLabel("Theme")
        theme_label.setObjectName("PopupSection")
        scale_label = QLabel("UI Scale")
        scale_label.setObjectName("PopupSection")

        self._theme_buttons = []
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        for value, label in (("light", "Light"), ("dark", "Dark")):
            btn = self._make_option(label, value, "theme", theme_row)
            self._theme_buttons.append(btn)

        self._scale_buttons = []
        scale_row = QHBoxLayout()
        scale_row.setSpacing(8)
        for value in (90, 100, 110, 125):
            btn = self._make_option(f"{value}%", value, "ui_scale", scale_row)
            self._scale_buttons.append(btn)

        done_button = QPushButton("Done")
        done_button.setObjectName("PopupCreate")
        done_button.clicked.connect(self.accept)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(22, 20, 22, 18)
        card_layout.setSpacing(8)
        card_layout.addWidget(title)
        card_layout.addSpacing(2)
        card_layout.addWidget(theme_label)
        card_layout.addLayout(theme_row)
        card_layout.addSpacing(6)
        card_layout.addWidget(scale_label)
        card_layout.addLayout(scale_row)
        card_layout.addStretch(1)
        card_layout.addWidget(done_button)

        self._sync_checkmarks()

    def _make_option(self, text, value, key, layout):
        btn = QPushButton(text)
        btn.setObjectName("OptionButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _=False, k=key, v=value: self._pick(k, v))
        layout.addWidget(btn, 1)
        return btn

    def _pick(self, key, value):
        self.settings[key] = value
        storage.save_settings(self.settings)
        owner = self.window_owner
        if owner is not None:
            owner.apply_ui(**self.settings)
        self._sync_checkmarks()

    def _sync_checkmarks(self):
        for btn in self._theme_buttons:
            btn.setProperty("active", str(self.settings["theme"]) == btn.text().lower())
            _repolish(btn)
        for btn in self._scale_buttons:
            btn.setProperty("active", str(self.settings["ui_scale"]) == btn.text().rstrip("%"))
            _repolish(btn)


class MessageScrollArea(QScrollArea):
    resized = Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class ContactRow(QFrame):
    def __init__(self, contact, m):
        super().__init__()
        self.setObjectName("ContactRow")
        self.contact = contact
        self.setFixedHeight(m["row_h"])

        color = AVATAR_COLORS[int(hashlib.md5(contact["id"].encode()).hexdigest(), 16) % len(AVATAR_COLORS)]
        initial = contact["name"].strip()[0].upper() if contact["name"].strip() else "?"

        avatar = QLabel(initial)
        avatar.setFixedSize(m["avatar"], m["avatar"])
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFont(QFont("Segoe UI", m["font_avatar"], QFont.DemiBold))
        avatar.setStyleSheet(
            f"background-color: {color}; color: #FFFFFF; border-radius: {m['avatar'] // 2}px;"
        )

        name = QLabel(contact["name"])
        name.setObjectName("ContactName")
        name.setMaximumWidth(m["preview_w"])
        self.preview_label = QLabel("")
        self.preview_label.setObjectName("ContactPreview")
        self.preview_label.setMaximumWidth(m["preview_w"])
        self.time_label = QLabel("")
        self.time_label.setObjectName("ContactTime")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        text_col.addWidget(name)
        text_col.addWidget(self.preview_label, 1, Qt.AlignVCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)
        layout.addWidget(avatar)
        layout.addLayout(text_col, 1)
        layout.addWidget(self.time_label, 0, Qt.AlignTop)

        self.preview_width = m["preview_w"]

    def set_preview(self, text, preview_time):
        fm = QFontMetrics(self.preview_label.font())
        shown = text.strip() if text.strip() else "No messages yet"
        elided = fm.elidedText(shown, Qt.ElideRight, self.preview_width)
        self.preview_label.setText(elided)
        self.time_label.setText(preview_time)


AVATAR_COLORS = [
    "#0A84FF", "#30D158", "#FF9F0A", "#FF375F",
    "#BF5AF2", "#64D2FF", "#FFD60A", "#AC8E68",
    "#FF6482", "#5E5CE6", "#00C7BE", "#A2845E",
]


class MainWindow(QWidget):
    request_chat = Signal(str, str, object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Messages")
        self.resize(960, 680)
        self.setMinimumSize(800, 560)

        self.contacts = []
        self.chats = {}
        self.current_contact = None
        self.pending = set()
        self._resize_timer = None
        self._scroll_anim = None
        self.typing_label = None
        self.typing_dots = 0

        self.settings = storage.load_settings()
        self.apply_ui(**self.settings)

        self.worker_thread = QThread(self)
        self.worker = ChatWorker()
        self.worker.moveToThread(self.worker_thread)
        self.request_chat.connect(self.worker.enqueue)
        self.worker.reply_ready.connect(self.on_reply)
        self.worker.request_failed.connect(self.on_error)
        self.worker_thread.start()

        self.typing_timer = QTimer(self)
        self.typing_timer.setInterval(400)
        self.typing_timer.timeout.connect(self._cycle_typing_dots)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar(), 0)
        root.addWidget(self._build_chat_pane(), 1)

        self.refresh_contacts()
        self.update_composer_state()

    def closeEvent(self, event):
        self.typing_timer.stop()
        self.worker_thread.quit()
        self.worker_thread.wait(5000)
        event.accept()

    # ------------------------------------------------------------------ theming

    def apply_ui(self, theme=None, ui_scale=None):
        if theme is not None:
            self.settings["theme"] = theme
        if ui_scale is not None:
            self.settings["ui_scale"] = ui_scale
        theme = self.settings["theme"]
        self.scale = max(0.8, min(1.5, self.settings["ui_scale"] / 100.0))
        self.m = build_metrics(self.scale)

        app = QApplication.instance()
        app.setFont(QFont("Segoe UI", 10))
        app.setStyleSheet(build_stylesheet(theme, self.scale))

        if hasattr(self, "sidebar_widget"):
            self.sidebar_widget.setFixedWidth(self.m["sidebar_w"])
        if hasattr(self, "sidebar_header"):
            self.sidebar_header.setFixedHeight(self.m["sidebar_header_h"])
        if hasattr(self, "chat_header_widget"):
            self.chat_header_widget.setFixedHeight(self.m["chat_header_h"])
        if hasattr(self, "add_button"):
            self.add_button.setFixedSize(self.m["add_btn"], self.m["add_btn"])
            self.add_button.setFont(QFont(ICON_FONT, self.m["font_icon_add"]))
        if hasattr(self, "settings_button"):
            self.settings_button.setFixedSize(self.m["add_btn"], self.m["add_btn"])
            self.settings_button.setFont(QFont(ICON_FONT, self.m["font_icon_add"]))
        if hasattr(self, "send_button"):
            self.send_button.setFixedSize(self.m["send_btn"], self.m["send_btn"])
            self.send_button.setFont(QFont(ICON_FONT, self.m["font_icon_send"]))
        if hasattr(self, "search_input"):
            self.search_input.setFixedHeight(max(30, int(34 * self.scale)))

        if hasattr(self, "contact_list"):
            self.refresh_contacts()
            if self.current_contact is not None:
                self.render_chat()

    # ------------------------------------------------------------------ UI building

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(self.m["sidebar_w"])
        self.sidebar_widget = sidebar

        header = QWidget()
        header.setObjectName("SidebarHeader")
        header.setFixedHeight(self.m["sidebar_header_h"])
        self.sidebar_header = header

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(0)
        title = QLabel("AI Messages")
        title.setObjectName("SidebarTitle")
        self.contact_count_label = QLabel("")
        self.contact_count_label.setObjectName("SidebarCount")
        title_box.addWidget(title)
        title_box.addWidget(self.contact_count_label)

        settings_button = QPushButton("\u2699")
        settings_button.setObjectName("SettingsButton")
        settings_button.setFixedSize(self.m["add_btn"], self.m["add_btn"])
        settings_button.setFont(QFont(ICON_FONT, self.m["font_icon_add"]))
        settings_button.setCursor(Qt.PointingHandCursor)
        settings_button.clicked.connect(self.open_settings)
        settings_button.setToolTip("Settings")
        self.settings_button = settings_button

        add_button = QPushButton("+")
        add_button.setObjectName("AddContactButton")
        add_button.setFixedSize(self.m["add_btn"], self.m["add_btn"])
        add_button.setFont(QFont(ICON_FONT, self.m["font_icon_add"]))
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(self.add_contact)
        add_button.setToolTip("Add contact")
        self.add_button = add_button

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 12, 4)
        header_layout.setSpacing(8)
        header_layout.addLayout(title_box, 1)
        header_layout.addWidget(settings_button, 0, Qt.AlignTop)
        header_layout.addWidget(add_button, 0, Qt.AlignTop)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search")
        self.search_input.setFixedHeight(max(30, int(34 * self.scale)))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)

        self.contact_list = QListWidget()
        self.contact_list.setObjectName("SidebarList")
        self.contact_list.setSelectionMode(QListWidget.SingleSelection)
        self.contact_list.currentItemChanged.connect(self.on_contact_selected)
        self.contact_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contact_list.customContextMenuRequested.connect(self._show_contact_menu)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 0, 8, 10)
        layout.setSpacing(4)
        layout.addWidget(header)
        layout.addWidget(self.search_input)
        layout.addWidget(self.contact_list, 1)

        return sidebar

    def _build_chat_pane(self):
        self.stack = QStackedWidget()

        placeholder = QWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.addStretch(1)
        placeholder_title = QLabel("AI Messages")
        placeholder_title.setObjectName("PlaceholderTitle")
        placeholder_title.setAlignment(Qt.AlignCenter)
        placeholder_hint = QLabel("Select a contact to start messaging")
        placeholder_hint.setObjectName("PlaceholderHint")
        placeholder_hint.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_title)
        placeholder_layout.addWidget(placeholder_hint)
        placeholder_layout.addStretch(1)

        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        chat_header = QWidget()
        chat_header.setObjectName("ChatHeader")
        chat_header.setFixedHeight(self.m["chat_header_h"])
        self.chat_header_widget = chat_header

        self.chat_title = QLabel("")
        self.chat_title.setObjectName("ChatTitle")
        self.chat_title.setAlignment(Qt.AlignCenter)
        self.chat_subtitle = QLabel(f"{chat_engine.MODEL} \u00b7 local")
        self.chat_subtitle.setObjectName("ChatSubtitle")
        self.chat_subtitle.setAlignment(Qt.AlignCenter)
        header_box = QVBoxLayout()
        header_box.setContentsMargins(0, 6, 0, 6)
        header_box.setSpacing(0)
        header_box.addWidget(self.chat_title)
        header_box.addWidget(self.chat_subtitle)
        header_layout = QHBoxLayout(chat_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addLayout(header_box)

        self.message_scroll = MessageScrollArea()
        self.message_scroll.setObjectName("MessageScroll")
        self.message_scroll.setWidgetResizable(True)
        self.message_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_scroll.resized.connect(self.on_chat_resized)

        self.message_container = QWidget()
        self.message_container.setObjectName("ChatBackground")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(14, 12, 14, 12)
        self.message_layout.setSpacing(4)
        self.message_scroll.setWidget(self.message_container)

        composer = QWidget()
        composer.setObjectName("ComposerContainer")
        self.composer_widget = composer
        self.composer_input = QLineEdit()
        self.composer_input.setObjectName("ComposerInput")
        self.composer_input.setPlaceholderText("iMessage")
        self.composer_input.returnPressed.connect(self.send_message)

        send_button = QPushButton("\u2708")
        send_button.setObjectName("SendButton")
        send_button.setFixedSize(self.m["send_btn"], self.m["send_btn"])
        send_button.setFont(QFont(ICON_FONT, self.m["font_icon_send"]))
        send_button.setCursor(Qt.PointingHandCursor)
        send_button.clicked.connect(self.send_message)
        self.send_button = send_button

        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(14, 8, 14, 10)
        composer_layout.setSpacing(10)
        composer_layout.addWidget(self.composer_input, 1)
        composer_layout.addWidget(send_button)

        chat_layout.addWidget(chat_header)
        chat_layout.addWidget(self.message_scroll, 1)
        chat_layout.addWidget(composer)

        self.stack.addWidget(placeholder)
        self.stack.addWidget(chat_panel)
        return self.stack

    # ------------------------------------------------------------------ contacts

    def refresh_contacts(self):
        self.contacts = storage.load_contacts()
        current_id = self.current_contact["id"] if self.current_contact else None
        if current_id is not None and current_id not in {c["id"] for c in self.contacts}:
            self.current_contact = None
            current_id = None

        self.contact_list.blockSignals(True)
        self.contact_list.clear()
        for contact in self.contacts:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, contact["id"])
            item.setSizeHint(QSize(0, self.m["row_h"]))
            self.contact_list.addItem(item)
            self.contact_list.setItemWidget(item, ContactRow(contact, self.m))
        self.contact_list.blockSignals(False)

        count = len(self.contacts)
        self.contact_count_label.setText(f"{count} contact{'s' if count != 1 else ''}")

        if current_id is not None:
            for i in range(self.contact_list.count()):
                item = self.contact_list.item(i)
                if item.data(Qt.UserRole) == current_id:
                    self.contact_list.setCurrentItem(item)
                    break
        else:
            self.current_contact = None
            self.stack.setCurrentIndex(0)
            self.update_composer_state()

        self._apply_filter()
        self._update_rows()
        self._update_selection_styles()

    def add_contact(self):
        popup = ContactPopup(self)
        if popup.exec() == QDialog.Accepted:
            contact = storage.save_contact(popup.name())
            self.refresh_contacts()
            for i in range(self.contact_list.count()):
                item = self.contact_list.item(i)
                if item.data(Qt.UserRole) == contact["id"]:
                    self.contact_list.setCurrentItem(item)
                    break

    def open_settings(self):
        popup = SettingsPopup(self)
        popup.exec()

    def _apply_filter(self):
        query = self.search_input.text().strip().lower()
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            contact = next((c for c in self.contacts if c["id"] == item.data(Qt.UserRole)), None)
            item.setHidden(bool(query) and contact is not None and query not in contact["name"].lower())

    def _update_rows(self):
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            row = self.contact_list.itemWidget(item)
            if not isinstance(row, ContactRow):
                continue
            cid = item.data(Qt.UserRole)
            msgs = self.chats.get(cid) or storage.load_messages(cid)
            if msgs:
                row.set_preview(msgs[-1]["content"], format_relative_time(msgs[-1].get("ts")))
            else:
                row.set_preview("", "")

    def _show_contact_menu(self, pos):
        item = self.contact_list.itemAt(pos)
        if item is None:
            return
        contact_id = item.data(Qt.UserRole)
        contact = next((c for c in self.contacts if c["id"] == contact_id), None)
        if contact is None:
            return

        menu = QMenu(self)
        delete_conv_action = QAction("Delete Conversation", self)
        delete_contact_action = QAction(f"Delete \u201c{contact['name']}\u201d", self)
        menu.addAction(delete_conv_action)
        menu.addSeparator()
        menu.addAction(delete_contact_action)

        chosen = menu.exec(self.contact_list.mapToGlobal(pos))

        if chosen is delete_conv_action:
            self.delete_conversation(contact_id)
            return

        if chosen is delete_contact_action:
            self.delete_contact(contact_id)

    def delete_conversation(self, contact_id):
        storage.delete_chat(contact_id)
        self.chats.pop(contact_id, None)
        self._update_rows()
        if self.current_contact and self.current_contact["id"] == contact_id:
            self.render_chat()
            self.composer_input.setFocus()

    def delete_contact(self, contact_id):
        if self.current_contact and self.current_contact["id"] == contact_id:
            self.current_contact = None
            self.chat_title.setText("")
            self.stack.setCurrentIndex(0)
        storage.delete_contact(contact_id)
        self.chats.pop(contact_id, None)
        self.refresh_contacts()

    def on_contact_selected(self, current, _previous):
        self._update_selection_styles()
        if current is None:
            self.current_contact = None
            self.stack.setCurrentIndex(0)
            self.update_composer_state()
            return

        contact_id = current.data(Qt.UserRole)
        contact = next((c for c in self.contacts if c["id"] == contact_id), None)
        if contact is None:
            return

        self.current_contact = contact
        if contact_id not in self.chats:
            self.chats[contact_id] = storage.load_messages(contact_id)

        self.chat_title.setText(contact["name"])
        self.stack.setCurrentIndex(1)
        self.render_chat()
        self.update_composer_state()
        self.composer_input.setFocus()

    def _update_selection_styles(self):
        theme = self.settings.get("theme", "light")
        selected_bg = "#E5E5EA" if theme == "light" else "#3A3A3C"
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            widget = self.contact_list.itemWidget(item)
            if isinstance(widget, ContactRow):
                if item is self.contact_list.currentItem():
                    widget.setStyleSheet(f"#ContactRow {{ background-color: {selected_bg}; border-radius: 12px; }}")
                else:
                    widget.setStyleSheet("#ContactRow { background-color: transparent; }")

    # ------------------------------------------------------------------ messaging

    def send_message(self):
        if self.current_contact is None:
            return
        text = self.composer_input.text().strip()
        if not text:
            return

        cid = self.current_contact["id"]
        self.composer_input.clear()

        msgs = self.chats.setdefault(cid, [])
        msgs.append({
            "role": "user",
            "content": text,
            "ts": datetime.now().isoformat(timespec="minutes"),
        })
        storage.save_messages(cid, msgs)

        self.pending.add(cid)
        self.render_chat()
        self.update_composer_state()
        self._update_rows()
        self.request_chat.emit(cid, self.current_contact["name"], msgs)

    def on_reply(self, cid, reply):
        self.pending.discard(cid)
        if cid not in {c["id"] for c in self.contacts}:
            return
        msgs = self.chats.setdefault(cid, [])
        msgs.append({
            "role": "assistant",
            "content": reply,
            "ts": datetime.now().isoformat(timespec="minutes"),
        })
        storage.save_messages(cid, msgs)
        is_current = self.current_contact and self.current_contact["id"] == cid
        if is_current:
            self.render_chat()
            self.composer_input.setFocus()
        self._update_rows()
        self.update_composer_state()

    def on_error(self, cid, error):
        self.pending.discard(cid)
        is_current = self.current_contact and self.current_contact["id"] == cid
        if is_current:
            self.render_chat()
            self._add_bubble(f"Error: {error}", kind="error")
            self._scroll_to_bottom()
            self.composer_input.setFocus()
        self.update_composer_state()

    def render_chat(self):
        layout = self.message_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.typing_label = None
        if self.current_contact is None:
            layout.addStretch(1)
            return

        cid = self.current_contact["id"]
        for msg in self.chats.get(cid, []):
            user = msg["role"] == "user"
            self._add_bubble(
                msg["content"],
                kind="user" if user else "other",
                time=format_bubble_time(msg.get("ts")),
            )

        if cid in self.pending:
            row, label = self._add_bubble("\u2022", kind="other", typing=True)
            self.typing_label = label
            self.typing_timer.start()

        layout.addStretch(1)
        self._scroll_to_bottom()

    def _cycle_typing_dots(self):
        if self.typing_label is None:
            self.typing_timer.stop()
            return
        self.typing_dots = (self.typing_dots + 1) % 4
        self.typing_label.setText("\u2022" * (self.typing_dots or 4))

    def _add_bubble(self, text, kind="other", time=None, typing=False):
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setMaximumWidth(self._bubble_max_width())

        if kind == "user":
            bubble.setObjectName("BubbleUser")
        elif kind == "error":
            bubble.setObjectName("BubbleError")
        else:
            bubble.setObjectName("BubbleOther")
            if typing:
                bubble.setObjectName("TypingDots")

        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(1)
        bubble_row = QHBoxLayout()
        bubble_row.setSpacing(0)

        if kind == "user":
            bubble_row.addStretch(1)
            bubble_row.addWidget(bubble)
        else:
            bubble_row.addWidget(bubble)
            bubble_row.addStretch(1)
        row_layout.addLayout(bubble_row)

        if time and not typing:
            time_label = QLabel(time)
            time_label.setObjectName("BubbleTime")
            time_row = QHBoxLayout()
            time_row.setSpacing(0)
            if kind == "user":
                time_row.addStretch(1)
                time_row.addWidget(time_label)
            else:
                time_row.addWidget(time_label)
                time_row.addStretch(1)
            row_layout.addLayout(time_row)

        self.message_layout.addWidget(row)
        return row, bubble

    def _bubble_max_width(self):
        width = self.message_scroll.viewport().width()
        return max(160, int(width * 0.68))

    def on_chat_resized(self):
        if self._resize_timer is not None:
            self._resize_timer.stop()
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.render_chat)
        self._resize_timer.start(120)

    def _scroll_to_bottom(self, animate=True):
        bar = self.message_scroll.verticalScrollBar()
        QTimer.singleShot(0, lambda: self._animate_scrollbar(bar, bar.maximum(), animate))

    def _animate_scrollbar(self, bar, target, animate):
        current = bar.value()
        if not animate or target <= current:
            bar.setValue(target)
            return
        if self._scroll_anim is not None:
            self._scroll_anim.stop()
            self._scroll_anim = None
        anim = QPropertyAnimation(bar, b"value", self)
        distance = target - current
        anim.setDuration(min(320, max(100, int(distance * 0.35))))
        anim.setStartValue(current)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda a=anim: self._on_scroll_done(a))
        anim.finished.connect(anim.deleteLater)
        self._scroll_anim = anim
        anim.start()

    def _on_scroll_done(self, anim):
        if self._scroll_anim is anim:
            self._scroll_anim = None

    def update_composer_state(self):
        enabled = (
            self.current_contact is not None
            and self.current_contact["id"] not in self.pending
        )
        self.composer_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(build_stylesheet("light", 1.0))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
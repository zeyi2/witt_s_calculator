import sys, os, json, re, subprocess
import traceback
import io
import webbrowser

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QTabWidget, QGridLayout, QComboBox, QLabel, QSizePolicy,
    QInputDialog, QSplitter, QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QCheckBox, QMessageBox, QLineEdit, QFormLayout, QListWidget,
    QListWidgetItem, QMenu, QAction, QTextBrowser
)
from PyQt5.QtCore import Qt
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

# ==============================
# Customization Storage
# ==============================
CUSTOMIZATION_FILE = "customizations.txt"
default_function_mappings = {
    "arcsin": "asin",
    "arccos": "acos",
    "arctan": "atan"
}


def load_customizations():
    if os.path.exists(CUSTOMIZATION_FILE):
        try:
            with open(CUSTOMIZATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}
    data.setdefault("language", "en")
    data.setdefault("labels", {})
    data.setdefault("mappings", default_function_mappings.copy())
    data.setdefault("dark_mode", False)
    data.setdefault("notes", [])
    return data


def save_customizations(custom_dict):
    with open(CUSTOMIZATION_FILE, "w", encoding="utf-8") as f:
        json.dump(custom_dict, f, indent=4, ensure_ascii=False)


CUSTOM_DICT = load_customizations()

# ==============================
# Global Stylesheets
# ==============================
dark_stylesheet = """
QWidget { background-color: #2b2b2b; color: #e0e0e0; }
QTextEdit { background-color: #3c3f41; color: #e0e0e0; min-height: 100px; }
QPushButton {
    background-color: #3c3f41; color: #e0e0e0;
    border: 1px solid #555; border-radius: 5px; padding: 8px 12px;
}
QPushButton:hover { border: 2px solid #ffcc00; }

QScrollBar:vertical {
    background: #3c3f41; width: 12px; margin: 0px; border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #555; min-height: 20px; border-radius: 5px;
}
QScrollBar:horizontal {
    background: #3c3f41; height: 12px; margin: 0px; border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #555; min-width: 20px; border-radius: 5px;
}

QComboBox {
    background-color: #3c3f41; color: #e0e0e0;
    border: 1px solid #555; border-radius: 5px;
    padding: 4px 8px; min-width: 200px;
}
QTableWidget { background-color: #3c3f41; color: #e0e0e0; }

/* TabBar with border and hover effect */
QTabBar::tab {
    background-color: #3c3f41; color: #000000;
    min-width: 180px;
    border: 1px solid #555;
    border-radius: 5px;
    margin-right: 2px;
    padding: 10px 20px;
}
QTabBar::tab:hover {
    border: 2px solid #ffcc00;
}
QTabBar::tab:selected {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 2px solid #ffcc00;
    border-radius: 5px;
}
QTabWidget::pane {
    border: 1px solid #555; top: -1px;
}
QTabBar QToolButton {
    background-color: transparent;
    border: none;
}
QTabBar QToolButton::left-arrow, QTabBar QToolButton::right-arrow {
    width: 10px;
    height: 10px;
}
QTabBar QToolButton:hover {
    background-color: rgba(0, 122, 204, 0.2);
    border-radius: 5px;
}
"""

light_stylesheet = """
QWidget { background-color: #ffffff; color: #000000; }
QTextEdit { background-color: #ffffff; color: #000000; min-height: 100px; }
QPushButton {
    background-color: #e0e0e0; color: #000000;
    border: 1px solid #aaa; border-radius: 5px; padding: 8px 12px;
}
QPushButton:hover { border: 2px solid #007acc; }

QScrollBar:vertical {
    background: #ffffff; width: 12px; margin: 0px; border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #ccc; min-height: 20px; border-radius: 5px;
}
QScrollBar:horizontal {
    background: #ffffff; height: 12px; margin: 0px; border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #ccc; min-width: 20px; border-radius: 5px;
}

QComboBox {
    background-color: #ffffff; color: #000000;
    border: 1px solid #aaa; border-radius: 5px;
    padding: 4px 8px; min-width: 200px;
}
QTableWidget { background-color: #ffffff; color: #000000; }

/* TabBar with border and hover effect */
QTabBar::tab {
    background: #e0e0e0; border: 1px solid #aaa;
    border-radius: 5px;
    border-bottom: none;
    padding: 10px 20px; margin-right: 2px;
    font-size: 12pt; min-width: 180px; color: #000000;
}
QTabBar::tab:hover {
    border: 2px solid #007acc;
}
QTabBar::tab:selected {
    background: #ffffff; border: 2px solid #007acc; border-radius: 5px;
    color: #000000;
}
QTabWidget::pane { border: 1px solid #aaa; top: -1px; }
QTabBar QToolButton {
    background-color: transparent;
    border: none;
}
QTabBar QToolButton::left-arrow, QTabBar QToolButton::right-arrow {
    width: 10px;
    height: 10px;
}
QTabBar QToolButton:hover {
    background-color: rgba(0, 122, 204, 0.2);
    border-radius: 5px;
}
"""


def set_dark_mode(enabled):
    if enabled:
        QApplication.instance().setStyleSheet(dark_stylesheet)
    else:
        QApplication.instance().setStyleSheet(light_stylesheet)


def update_dark_mode_state(enabled):
    CUSTOM_DICT["dark_mode"] = enabled
    save_customizations(CUSTOM_DICT)
    set_dark_mode(enabled)


# ==============================
# LaTeX Parsing
# ==============================
try:
    from sympy.parsing.latex import parse_latex
except ImportError:
    def parse_latex(latex_str):
        raise NotImplementedError("Install antlr4-python3-runtime for LaTeX parsing.")

# ==============================
# Localization
# ==============================
translations = {
    "en": {
        "app_title": "witt's Calculator",
        "standard_tab": "Standard",
        "latex_tab": "LaTeX (Experimental)",
        "settings_tab": "Settings",
        "enter_expression": "Enter expression (e.g. 2*sin(pi/4) + ln(10))",
        "mode_rad": "Mode: RAD",
        "mode_deg": "Mode: DEG",
        "clear": "C",
        "backspace": "<--",
        "sin": "sin",
        "cos": "cos",
        "tan": "tan",
        "ln": "ln",
        "open_paren": "(",
        "close_paren": ")",
        "power": "**",
        "divide": "/",
        "multiply": "*",
        "subtract": "-",
        "add": "+",
        "dot": ".",
        "equals": "EXE",
        "enter_latex": r"Enter LaTeX expression (e.g. \frac{1}{2} + \sqrt{4})",
        "error_prefix": "<ERROR>: ",
        "divider": "------------------------",
        "choose_language": "Language:",
        "english": "English",
        "chinese": "现代汉语 (Simplified Chinese)",
        "custom_help":
            "----------- TIPS -----------\n"
            "(1) Use 'pi' for \u03c0 and 'oo' for \u221E.\n"
            "(2) Right-click any custom button to change its label.\n"
            "(3) Right-click a history entry to delete it.\n"
            "(4) Mappings (set in the Mapping Editor) replace function names (e.g. arctan -> atan).",
        "latex_help": "",
        "list_mappings": "Mapping Editor...",
        "mapping_editor": "Mapping Editor",
        "open_custom_file": "Open Customizations File",
        "open_in_file_browser": "Open in File Browser",
        "mapping_name": "Before",
        "mapping_replacement": "After",
        "add_mapping": "Add Mapping",
        "remove_mapping": "Remove Selected Mapping",
        "revert_mappings": "Reset All Mappings",
        "revert_customizations": "Reset Button Customizations",
        "ok": "OK",
        "customize_button_label": "Customize Buttons",
        "enter_new_label": "Enter new label:",
        "prompt_add_mapping_name": "Enter mapping name (e.g. arcsin):",
        "prompt_add_mapping_replacement": "Enter replacement (e.g. asin):",
        "dark_mode": "Dark Mode",
        "mapping_help": "Mappings replace text in your input. For example, if you set 'arctan' to 'atan', every occurrence is replaced.",
        "copyright": "witt's Calculator Beta 1.0\n"
                     "By witt\n"
                     "Icon by 3s.",
        "help": "Open help.html in Browser",
        "open_notes": "Notes...",
        "notebook": "Notes",
        "clear_history": "Clear History",
        "save_analytical": "Save Analytical",
        "save_approx": "Save Approximation"
    },
    "zh": {
        "app_title": "witt's Calculator",
        "standard_tab": "标准",
        "latex_tab": "LaTeX（实验性）",
        "settings_tab": "设置",
        "enter_expression": "输入表达式（如2*sin(pi/4) + ln(10)）",
        "mode_rad": "当前：弧度制",
        "mode_deg": "当前：角度制",
        "clear": "C",
        "backspace": "<--",
        "sin": "sin",
        "cos": "cos",
        "tan": "tan",
        "ln": "ln",
        "open_paren": "(",
        "close_paren": ")",
        "power": "**",
        "divide": "/",
        "multiply": "*",
        "subtract": "-",
        "add": "+",
        "dot": ".",
        "equals": "EXE",
        "enter_latex": r"输入LaTeX表达式（如\frac{1}{2} + \sqrt{4}）",
        "advanced_help_command": "/help",
        "advanced_help_text": "高级帮助:",  # TODO
        "error_prefix": "<错误>: ",
        "divider": "------------------------",
        "choose_language": "语言:",
        "english": "英语（English）",
        "chinese": "现代汉语",
        "custom_help":
            "----------- 提示 -----------\n"
            "(1) pi 表示 \u03c0；oo 表示 \u221E\n"
            "(2) 右键自定义按钮以配置其标签\n"
            "(3) 右键历史记录可将其删除\n"
            "(4) 映射（在设置中配置）可替换函数名称（如 arctan -> atan）",
        "latex_help": "",
        "list_mappings": "映射管理器...",
        "mapping_editor": "映射管理器",
        "open_custom_file": "打开配置文件",
        "open_in_file_browser": "打开所在目录",
        "mapping_name": "映射前",
        "mapping_replacement": "映射后",
        "add_mapping": "添加映射",
        "remove_mapping": "移除选定映射",
        "revert_mappings": "重置所有映射",
        "revert_customizations": "重置自定义按钮",
        "ok": "确定",
        "customize_button_label": "自定义按钮",
        "enter_new_label": "输入新标签：",
        "prompt_add_mapping_name": "输入映射名称（如 arcsin）：",
        "prompt_add_mapping_replacement": "输入替换（如 asin）：",
        "dark_mode": "深色界面",
        "mapping_help": "映射用于替换输入文本。例如，如果你设置 'arctan' 的映射为 'atan'，则所有 'arctan' 都会被替换。",
        "copyright": "witt's Calculator Beta 1.0\n"
                     "制作：witt\n"
                     "图标绘制：3s.",
        "help": "打开帮助文件（本地浏览器）",
        "open_notes": "笔记本...",
        "notebook": "笔记本",
        "clear_history": "清除历史记录",
        "save_analytical": "保存解析值",
        "save_approx": "保存近似值"
    }
}


def t(key):
    lang = CUSTOM_DICT.get("language", "en")
    return translations[lang].get(key, key)


# -----------------------------
# NoteEditDialog
# -----------------------------
class NoteEditDialog(QDialog):
    def __init__(self, note=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Note")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.note = note if note is not None else {"name": "", "value": "", "type": ""}
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.name_edit = QLineEdit(self.note.get("name", ""))
        self.value_edit = QLineEdit(self.note.get("value", ""))
        self.type_edit = QLineEdit(self.note.get("type", ""))
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Value:", self.value_edit)
        layout.addRow("Type:", self.type_edit)
        btn = QPushButton("Save")
        btn.clicked.connect(self.accept)
        layout.addRow(btn)
        self.setLayout(layout)

    def get_note(self):
        return {"name": self.name_edit.text(),
                "value": self.value_edit.text(),
                "type": self.type_edit.text()}


# -----------------------------
# NotesEditorWindow
# -----------------------------
class NotesEditorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("notebook"))
        self.resize(800, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Value", "Input"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Note")
        self.btn_add.clicked.connect(self.add_note)
        btn_layout.addWidget(self.btn_add)
        self.btn_delete = QPushButton("Delete Note")
        self.btn_delete.clicked.connect(self.delete_note)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.load_notes()

    def load_notes(self):
        notes = CUSTOM_DICT.get("notes", [])
        self.table.setRowCount(len(notes))
        for i, note in enumerate(notes):
            self.table.setItem(i, 0, QTableWidgetItem(note.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(note.get("type", "")))
            self.table.setItem(i, 2, QTableWidgetItem(note.get("value", "")))
            self.table.setItem(i, 3, QTableWidgetItem(note.get("input", "")))

    def add_note(self):
        dlg = NoteEditDialog(None, self)
        if dlg.exec_():
            new_note = dlg.get_note()
            new_note["input"] = ""
            notes = CUSTOM_DICT.get("notes", [])
            notes.append(new_note)
            CUSTOM_DICT["notes"] = notes
            save_customizations(CUSTOM_DICT)
            self.load_notes()

    def delete_note(self):
        row = self.table.currentRow()
        if row < 0:
            return
        notes = CUSTOM_DICT.get("notes", [])
        del notes[row]
        CUSTOM_DICT["notes"] = notes
        save_customizations(CUSTOM_DICT)
        self.load_notes()


# -----------------------------
# HistoryEntry
# -----------------------------
class HistoryEntry(QFrame):
    def __init__(self, input_str, analytical_str, approx_str=None, error=False, parent_notes_callback=None):
        super().__init__()
        self.input_str = input_str
        self.analytical_str = analytical_str
        self.approx_str = approx_str
        self.error = error
        self.parent_notes_callback = parent_notes_callback
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        self.lbl_input = QLabel(self.input_str)
        self.lbl_input.setAlignment(Qt.AlignLeft)
        self.lbl_input.setStyleSheet("font-size: 14pt;")
        layout.addWidget(self.lbl_input)
        if self.error:
            self.lbl_error = QLabel(self.analytical_str)
            self.lbl_error.setAlignment(Qt.AlignRight)
            self.lbl_error.setStyleSheet("color: red; font-size: 14pt;")
            layout.addWidget(self.lbl_error)
        else:
            if CUSTOM_DICT.get("dark_mode", False):
                analytical_color = "#00ff00"
                approx_color = "#00ccff"
            else:
                analytical_color = "darkgreen"
                approx_color = "blue"
            self.lbl_analytical = QLabel(self.analytical_str)
            self.lbl_analytical.setAlignment(Qt.AlignRight)
            self.lbl_analytical.setStyleSheet(f"color: {analytical_color}; font-weight: bold; font-size: 14pt;")
            layout.addWidget(self.lbl_analytical)
            self.lbl_approx = QLabel(self.approx_str)
            self.lbl_approx.setAlignment(Qt.AlignRight)
            self.lbl_approx.setStyleSheet(f"color: {approx_color}; font-weight: bold; font-size: 14pt;")
            layout.addWidget(self.lbl_approx)
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 10, 0, 10)
            btn_layout.addStretch()
            self.btn_save_analytical = QPushButton(t("save_analytical"))
            self.btn_save_analytical.setFixedSize(250, 50)
            self.btn_save_analytical.clicked.connect(lambda: self.save_note("Analytical"))
            btn_layout.addWidget(self.btn_save_analytical)
            self.btn_save_approx = QPushButton(t("save_approx"))
            self.btn_save_approx.setFixedSize(250, 50)
            self.btn_save_approx.clicked.connect(lambda: self.save_note("Approximation"))
            btn_layout.addWidget(self.btn_save_approx)
            layout.addLayout(btn_layout)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = QAction("Delete Entry", self)
        delete_action.triggered.connect(lambda: self.delete_self())
        menu.addAction(delete_action)
        menu.exec_(event.globalPos())

    def delete_self(self):
        self.setParent(None)
        self.deleteLater()

    def save_note(self, result_type):
        note_name, ok = QInputDialog.getText(self, "Save Note", "Enter note name:",
                                             flags=Qt.WindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
                                             )
        if ok and note_name:
            note = {
                "name": note_name,
                "type": result_type,
                "value": self.analytical_str if result_type == "analytical" else self.approx_str,
                "input": self.input_str,
            }
            notes = CUSTOM_DICT.get("notes", [])
            notes.append(note)
            CUSTOM_DICT["notes"] = notes
            save_customizations(CUSTOM_DICT)
            if self.parent_notes_callback:
                self.parent_notes_callback()


# -----------------------------
# HistoryWidget
# -----------------------------
class HistoryWidget(QScrollArea):
    def __init__(self, parent=None, notes_callback=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setSpacing(5)
        self.vbox.addStretch()
        self.setWidget(self.container)
        self.notes_callback = notes_callback

    def add_entry(self, input_str, analytical_str, approx_str=None, error=False):
        entry = HistoryEntry(input_str, analytical_str, approx_str, error, parent_notes_callback=self.notes_callback)
        self.vbox.insertWidget(self.vbox.count() - 1, entry)

    def clear_entries(self):
        for i in reversed(range(self.vbox.count() - 1)):
            widget = self.vbox.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()


# -----------------------------
# CustomButton
# -----------------------------
class CustomButton(QPushButton):
    def __init__(self, id_key, translation_key, callback, labels_dict):
        super().__init__()
        self.id_key = id_key
        self.translation_key = translation_key
        self.labels_dict = labels_dict
        self.custom_text = self.labels_dict.get(id_key, t(translation_key))
        self.setText(self.custom_text)
        self.callback = callback
        self.clicked.connect(lambda: self.callback(self.custom_text))
        self.setMinimumSize(60, 60)

    def updateTranslation(self):
        self.custom_text = self.labels_dict.get(self.id_key, t(self.translation_key))
        self.setText(self.custom_text)

    def contextMenuEvent(self, event):
        # All customizable buttons allow editing
        new_label, ok = QInputDialog.getText(self, t("customize_button_label"),
                                             t("enter_new_label"), text=self.custom_text,
                                             flags=Qt.WindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
                                             )
        if ok:
            if new_label == "":
                self.custom_text = t(self.translation_key)
                if self.id_key in self.labels_dict:
                    del self.labels_dict[self.id_key]
            else:
                self.custom_text = new_label
                self.labels_dict[self.id_key] = new_label
            self.setText(self.custom_text)
            CUSTOM_DICT["labels"] = self.labels_dict
            save_customizations(CUSTOM_DICT)


# -----------------------------
# StandardCalculatorTab
# -----------------------------
class StandardCalculatorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.angle_mode = 'rad'
        self.custom_buttons = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Input section
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText(t("enter_expression"))
        self.input_field.setStyleSheet("font-size: 16pt;")
        self.input_field.setFixedHeight(max(min(self.input_field.fontMetrics().lineSpacing() + 20, 200), 120))
        self.input_field.textChanged.connect(self.adjust_input_height)
        input_layout.addWidget(self.input_field)

        mode_layout = QHBoxLayout()
        self.mode_button = QPushButton(t("mode_rad"))
        self.mode_button.setStyleSheet("font-size: 14pt; padding: 5px;")
        self.mode_button.clicked.connect(self.toggle_angle_mode)
        mode_layout.addWidget(self.mode_button)

        self.open_notes_btn = QPushButton(t("open_notes"))
        self.open_notes_btn.setStyleSheet("font-size: 14pt; padding: 5px;")
        self.open_notes_btn.clicked.connect(lambda: NotesEditorWindow(self).show())
        mode_layout.addWidget(self.open_notes_btn)

        self.clear_history_btn = QPushButton(t("clear_history"))
        self.clear_history_btn.setStyleSheet("font-size: 14pt; padding: 5px;")
        self.clear_history_btn.clicked.connect(self.confirm_clear_history)
        mode_layout.addWidget(self.clear_history_btn)

        mode_layout.addStretch()
        input_layout.addLayout(mode_layout)

        self.hint_label = QLabel(
            t("custom_help")
        )
        self.hint_label.setStyleSheet("font-size: 10pt; color: gray;")
        self.hint_label.setWordWrap(True)
        input_layout.addWidget(self.hint_label)
        main_layout.addWidget(input_widget)

        # Button grid
        btn_widget = QWidget()
        btn_layout = QVBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)
        grid = QGridLayout()
        grid.setSpacing(5)

        rows = [
            [("clear", "clear", self.clear, False),
             ("backspace", "backspace", self.backspace, False),
             ("sin", "sin", self.append_text, False),
             ("cos", "cos", self.append_text, False),
             ("tan", "tan", self.append_text, False)],

            [("ln", "ln", self.append_text, False),
             ("open_paren", "open_paren", self.append_text, False),
             ("close_paren", "close_paren", self.append_text, False),
             ("power", "power", self.append_text, False),
             ("custom1", "custom1", self.append_text, True)
             ],

            [("7", "7", self.append_text, False),
             ("8", "8", self.append_text, False),
             ("9", "9", self.append_text, False),
             ("divide", "divide", self.append_text, False),
             ("custom2", "custom2", self.append_text, True)
             ],

            [("4", "4", self.append_text, False),
             ("5", "5", self.append_text, False),
             ("6", "6", self.append_text, False),
             ("multiply", "multiply", self.append_text, False),
             ("custom3", "custom3", self.append_text, True)
             ],

            [("1", "1", self.append_text, False),
             ("2", "2", self.append_text, False),
             ("3", "3", self.append_text, False),
             ("subtract", "subtract", self.append_text, False),
             ("custom4", "custom4", self.append_text, True)
             ],

            [("0", "0", self.append_text, False),
             ("dot", "dot", self.append_text, False),
             ("equals", "equals", self.calculate, False),
             ("add", "add", self.append_text, False),
             ("custom5", "custom5", self.append_text, True)]
        ]

        # Build grid
        for r, row in enumerate(rows):
            for c, item in enumerate(row):
                id_key, trans_key, callback, customizable = item
                btn = None
                if customizable:
                    # Create a customizable button
                    btn = CustomButton(id_key, trans_key, callback, CUSTOM_DICT.get("labels", {}))
                    btn.setStyleSheet("""
                                    font-size: 14pt; padding: 5px;
                                   
                                    """)
                    self.custom_buttons.append(btn)
                else:
                    # Normal button
                    disp_text = t(trans_key)
                    btn = QPushButton(disp_text)
                    btn.setMinimumSize(60, 60)
                    btn.setStyleSheet("""
                                       font-size: 14pt; padding: 5px;
                                      
                                       """)
                    if callback in (self.clear, self.backspace, self.calculate):
                        btn.clicked.connect(callback)
                    else:
                        btn.clicked.connect(lambda checked, txt=disp_text: self.append_text(txt))

                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                grid.addWidget(btn, r, c)

        btn_layout.addLayout(grid)
        btn_widget.setLayout(btn_layout)
        input_layout.addWidget(btn_widget)

        # History area
        self.history_widget = HistoryWidget()
        main_layout.addWidget(self.history_widget, stretch=1)
        self.setLayout(main_layout)

    def adjust_input_height(self):
        fm = self.input_field.fontMetrics()
        lines = self.input_field.document().blockCount()
        new_height = max(min(lines * fm.lineSpacing() + 20, 200), 120)
        self.input_field.setFixedHeight(new_height)

    def append_text(self, text):
        cursor = self.input_field.textCursor()
        cursor.insertText(text)

    def clear(self):
        self.input_field.clear()

    def backspace(self):
        text = self.input_field.toPlainText()
        self.input_field.setPlainText(text[:-1])

    def toggle_angle_mode(self):
        if self.angle_mode == 'rad':
            self.angle_mode = 'deg'
            self.mode_button.setText(t("mode_deg"))
        else:
            self.angle_mode = 'rad'
            self.mode_button.setText(t("mode_rad"))

    def calculate(self):
        expr_str = (self.input_field.toPlainText()
                    # .strip()
                    .replace("\n", "")
                    .replace("\t", "")
                    .replace(" ", "")
                    )
        if not expr_str:
            return
        # Apply mappings
        for name, repl in CUSTOM_DICT.get("mappings", default_function_mappings).items():
            expr_str = expr_str.replace(name, repl)
        try:
            if self.angle_mode == 'deg':
                trig_sin = lambda x: sp.sin(x * sp.pi / 180)
                trig_cos = lambda x: sp.cos(x * sp.pi / 180)
                trig_tan = lambda x: sp.tan(x * sp.pi / 180)
            else:
                trig_sin = sp.sin
                trig_cos = sp.cos
                trig_tan = sp.tan

            local_dict = {
                "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "ln": sp.log,
                "sin": trig_sin, "cos": trig_cos, "tan": trig_tan,
                "pi": sp.pi, "e": sp.E
            }
            expr = parse_expr(expr_str, local_dict=local_dict, evaluate=True)
            approx_str = str(sp.N(expr))
            analytical_str = str(sp.nsimplify(expr, [sp.pi, sp.E]))
            self.history_widget.add_entry(
                self.input_field.toPlainText(),
                analytical_str, approx_str
            )
        except Exception as e:
            self.history_widget.add_entry(
                self.input_field.toPlainText(),
                t("error_prefix") + str(e), error=True
            )

    def revert_customizations(self):
        for btn in self.custom_buttons:
            key = btn.id_key
            if key in CUSTOM_DICT.get("labels", {}):
                del CUSTOM_DICT["labels"][key]
            btn.custom_text = t(btn.translation_key)
            btn.setText(t(btn.translation_key))
        save_customizations(CUSTOM_DICT)

    def confirm_clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history_widget.clear_entries()

    def updateTranslations(self):
        self.input_field.setPlaceholderText(t("enter_expression"))
        self.mode_button.setText(
            t("mode_rad") if self.angle_mode == 'rad' else t("mode_deg")
        )
        for btn in self.custom_buttons:
            btn.updateTranslation()
        self.open_notes_btn.setText(t("open_notes"))
        self.clear_history_btn.setText(t("clear_history"))
        self.hint_label.setText(t("custom_help"))


# -----------------------------
# LatexCalculatorTab
# -----------------------------
class LatexCalculatorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        self.latex_input = QTextEdit()
        self.latex_input.setPlaceholderText(t("enter_latex"))
        self.latex_input.setStyleSheet("font-size: 16pt;")
        self.latex_input.setFixedHeight(max(min(self.latex_input.fontMetrics().lineSpacing() + 20, 200), 120))
        self.latex_input.textChanged.connect(self.adjust_input_height)
        top_layout.addWidget(self.latex_input)
        btn_layout = QHBoxLayout()
        self.calc_button = QPushButton(t("equals"))
        self.calc_button.setStyleSheet("font-size: 14pt; padding: 5px;")
        self.calc_button.setMinimumWidth(180)
        self.calc_button.clicked.connect(self.calculate)
        btn_layout.addWidget(self.calc_button)
        btn_layout.addStretch()
        top_layout.addLayout(btn_layout)
        top_widget.setLayout(top_layout)
        splitter.addWidget(top_widget)
        self.history_widget = HistoryWidget()
        splitter.addWidget(self.history_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def adjust_input_height(self):
        fm = self.latex_input.fontMetrics()
        lines = self.latex_input.document().blockCount()
        new_height = max(min(lines * fm.lineSpacing() + 20, 200), 120)
        self.latex_input.setFixedHeight(new_height)

    def calculate(self):
        expr_str = self.latex_input.toPlainText().strip()  # .replace("\n", "")
        if not expr_str:
            return
        try:
            result = parse_latex(expr_str)
            result_str = str(sp.N(result))
            self.history_widget.add_entry(expr_str, result_str)
            self.latex_input.clear()
        except Exception as e:
            self.history_widget.add_entry(expr_str, t("error_prefix") + str(e), error=True)

    def updateTranslations(self):
        self.latex_input.setPlaceholderText(t("enter_latex"))
        self.calc_button.setText(t("equals"))


# -----------------------------
# MappingEditorWindow
# -----------------------------
class MappingEditorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("mapping_editor"))
        self.resize(400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([t("mapping_name"), t("mapping_replacement")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(t("add_mapping"))
        self.add_btn.clicked.connect(self.add_mapping)
        btn_layout.addWidget(self.add_btn)
        self.remove_btn = QPushButton(t("remove_mapping"))
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.remove_btn)
        self.revert_btn = QPushButton(t("revert_mappings"))
        self.revert_btn.clicked.connect(self.revert_mappings)
        btn_layout.addWidget(self.revert_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.ok_btn = QPushButton(t("ok"))
        self.ok_btn.clicked.connect(self.accept)
        layout.addWidget(self.ok_btn, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.load_table()

    def load_table(self):
        mappings = CUSTOM_DICT.get("mappings", default_function_mappings)
        items = list(mappings.items())
        self.table.setRowCount(len(items))
        for i, (name, repl) in enumerate(items):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            repl_item = QTableWidgetItem(repl)
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, repl_item)

    def add_mapping(self):
        name, ok1 = QInputDialog.getText(self, t("add_mapping"), t("prompt_add_mapping_name"))
        if not ok1 or not name:
            return
        repl, ok2 = QInputDialog.getText(self, t("add_mapping"), t("prompt_add_mapping_replacement"))
        if ok2 and repl:
            mappings = CUSTOM_DICT.get("mappings", {})
            mappings[name] = repl
            CUSTOM_DICT["mappings"] = mappings
            save_customizations(CUSTOM_DICT)
            self.load_table()

    def remove_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        name_item = self.table.item(row, 0)
        name = name_item.text()
        mappings = CUSTOM_DICT.get("mappings", {})
        if name in mappings:
            del mappings[name]
            CUSTOM_DICT["mappings"] = mappings
            save_customizations(CUSTOM_DICT)
            self.load_table()

    def revert_mappings(self):
        reply = QMessageBox.question(
            self, "Revert Mappings",
            "Are you sure you want to revert all mappings?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            CUSTOM_DICT["mappings"] = default_function_mappings.copy()
            save_customizations(CUSTOM_DICT)
            self.load_table()


# -----------------------------
# SettingsTab
# -----------------------------
class SettingsTab(QWidget):
    def __init__(self, update_callback, revert_custom_callback):
        super().__init__()
        self.update_callback = update_callback
        self.revert_custom_callback = revert_custom_callback
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.lang_label = QLabel(t("choose_language"))
        self.lang_label.setStyleSheet("font-size: 14pt;")
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.lang_label)
        self.combo = QComboBox()
        self.combo.setStyleSheet("""
QComboBox {
    background-color: #f8f9fa;
    border: 2px solid #ced4da;
    border-radius: 8px;
    padding: 8px 15px;
    selection-background-color: #007bff;
    selection-color: white;
    color: #333;
    font-size: 24px;
    font-family: "Arial", "Microsoft YaHei", sans-serif;
}

QComboBox:hover {
    border-color: #007bff;
}

QComboBox:focus {
    border-color: #0056b3;
    outline: none;
}

/* Remove the drop-down button */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 0px;
    border: none;
}

/* Ensure no arrow image is shown */
QComboBox::down-arrow {
    image: none;
}

QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #ced4da;
    border-radius: 6px;
    selection-background-color: #007bff;
    selection-color: white;
    padding: 6px;
    font-size: 16px;
    font-family: "Arial", "Microsoft YaHei", sans-serif;
}

QComboBox QAbstractItemView::item {
    padding: 10px 15px;
    border-radius: 6px;
    font-size: 16px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #e9ecef;
    color: #007bff;
}
        """)
        self.combo.setMinimumWidth(400)
        self.combo.addItem(t("english"), "en")
        self.combo.addItem(t("chinese"), "zh")
        # Set current index based on saved language
        if CUSTOM_DICT.get("language", "en") == "en":
            self.combo.setCurrentIndex(0)
        else:
            self.combo.setCurrentIndex(1)
        self.combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.combo)
        lang_layout.addStretch()
        main_layout.addLayout(lang_layout)

        self.dark_mode_cb = QCheckBox(t("dark_mode"))
        self.dark_mode_cb.setStyleSheet("font-size: 14pt;")
        self.dark_mode_cb.setChecked(CUSTOM_DICT.get("dark_mode", False))
        self.dark_mode_cb.stateChanged.connect(lambda state: update_dark_mode_state(state == Qt.Checked))
        main_layout.addWidget(self.dark_mode_cb)

        revert_layout = QHBoxLayout()
        self.revert_custom_btn = QPushButton(t("revert_customizations"))
        self.revert_custom_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.revert_custom_btn.setStyleSheet("font-size: 14pt; padding: 8px 12px;")
        self.revert_custom_btn.clicked.connect(lambda: self.confirm_revert("labels"))
        revert_layout.addWidget(self.revert_custom_btn)
        revert_layout.addStretch()
        main_layout.addLayout(revert_layout)

        self.mappings_btn = QPushButton(t("list_mappings"))
        self.mappings_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.mappings_btn.setStyleSheet("font-size: 14pt; padding: 8px 12px;")
        self.mappings_btn.clicked.connect(self.open_mapping_editor)
        main_layout.addWidget(self.mappings_btn)

        file_btn_layout = QHBoxLayout()
        self.open_btn = QPushButton(t("open_custom_file"))
        self.open_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.open_btn.setStyleSheet("font-size: 14pt; padding: 8px 12px;")
        self.open_btn.clicked.connect(self.open_custom_file)
        file_btn_layout.addWidget(self.open_btn)

        self.browser_btn = QPushButton(t("open_in_file_browser"))
        self.browser_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.browser_btn.setStyleSheet("font-size: 14pt; padding: 8px 12px;")
        self.browser_btn.clicked.connect(self.open_in_file_browser)
        file_btn_layout.addWidget(self.browser_btn)
        file_btn_layout.addStretch()
        main_layout.addLayout(file_btn_layout)

        self.help_btn = QPushButton(t("help"))
        self.help_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.help_btn.setStyleSheet("font-size: 14pt; padding: 8px 12px;")
        self.help_btn.clicked.connect(self.open_help_doc)
        main_layout.addWidget(self.help_btn)

        # icon display
        main_layout.addStretch()

        icon_label = QLabel()
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        icon_pixmap = QPixmap(os.path.join(base_path, "original.jpg")).scaled(256, 256, Qt.KeepAspectRatio,
                                                                              Qt.SmoothTransformation)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(icon_label)

        # copyright text

        self.copyright_label = QLabel(t("copyright"))
        self.copyright_label.setStyleSheet("font-size: 14pt; color: gray;")
        self.copyright_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.copyright_label)
        self.setLayout(main_layout)

    def change_language(self, index):
        global current_lang
        current_lang = self.combo.itemData(index)
        CUSTOM_DICT["language"] = current_lang
        save_customizations(CUSTOM_DICT)
        self.update_callback()

    def open_custom_file(self):
        if os.path.exists(CUSTOMIZATION_FILE):
            if sys.platform.startswith('win'):
                os.startfile(CUSTOMIZATION_FILE)
            elif sys.platform.startswith('darwin'):
                subprocess.call(('open', CUSTOMIZATION_FILE))
            else:
                subprocess.call(('xdg-open', CUSTOMIZATION_FILE))

    def open_in_file_browser(self):
        folder = os.path.dirname(os.path.abspath(CUSTOMIZATION_FILE))
        if os.path.exists(folder):
            if sys.platform.startswith('win'):
                os.startfile(folder)
            elif sys.platform.startswith('darwin'):
                subprocess.call(('open', folder))
            else:
                subprocess.call(('xdg-open', folder))

    def open_help_doc(self):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        html_path = os.path.join(base_path, "help.html")
        webbrowser.open(f"file://{html_path}")

    def open_mapping_editor(self):
        editor = MappingEditorWindow(self)
        editor.show()

    def confirm_revert(self, which):
        if which == "labels":
            reply = QMessageBox.question(self, "Revert Button Labels",
                                         "Are you sure you want to revert all button labels?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.revert_custom_callback()
        elif which == "mappings":
            reply = QMessageBox.question(self, "Revert Mappings",
                                         "Are you sure you want to revert all mappings?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                CUSTOM_DICT["mappings"] = default_function_mappings.copy()
                save_customizations(CUSTOM_DICT)

    def updateTranslations(self):
        self.lang_label.setText(t("choose_language"))
        self.combo.blockSignals(True)
        self.combo.setItemText(0, t("english"))
        self.combo.setItemText(1, t("chinese"))
        self.combo.blockSignals(False)
        self.revert_custom_btn.setText(t("revert_customizations"))
        self.mappings_btn.setText(t("list_mappings"))
        self.open_btn.setText(t("open_custom_file"))
        self.browser_btn.setText(t("open_in_file_browser"))
        self.help_btn.setText(t("help"))
        self.copyright_label.setText(t("copyright"))
        self.dark_mode_cb.setText(t("dark_mode"))
        self.dark_mode_cb.setChecked(CUSTOM_DICT.get("dark_mode", False))
        self.dark_mode_cb.setText(t("dark_mode"))
        self.setWindowTitle(t("app_title"))

        # If user changes language, we might also want to re-check the current index
        if CUSTOM_DICT.get("language", "en") == "en":
            self.combo.setCurrentIndex(0)
        else:
            self.combo.setCurrentIndex(1)

        # Finally update the label again
        self.lang_label.setText(t("choose_language"))


# ==============================
# Main Application
# ==============================
class CalculatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.resize(600, 1100)

        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        app.setWindowIcon(QIcon(os.path.join(base_path, "icon.ico")))

        self.tabs = QTabWidget()

        self.tabs.setUsesScrollButtons(False)

        self.standard_tab = StandardCalculatorTab()
        self.latex_tab = LatexCalculatorTab()
        self.settings_tab = SettingsTab(self.updateTranslations, self.standard_tab.revert_customizations)

        self.tabs.addTab(self.standard_tab, t("standard_tab"))
        self.tabs.addTab(self.latex_tab, t("latex_tab"))
        self.tabs.addTab(self.settings_tab, t("settings_tab"))

        # TabBar with a border, hover effect, and min-width of 180px
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #aaa;
                border-radius: 5px;
                border-bottom: none;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 12pt;
                min-width: 300px;
                min-height: 40px;
                color: #000000;
            }
            QTabBar::tab:hover {
                border: 2px solid #007acc;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border: 2px solid #007acc;
                border-radius: 5px;
                color: #000000;
            }
            QTabWidget::pane {
                border: 1px solid #aaa;
                top: -1px;
            }
        """)

        self.setCentralWidget(self.tabs)

    def updateTranslations(self):
        self.standard_tab.updateTranslations()
        self.latex_tab.updateTranslations()
        self.settings_tab.updateTranslations()

        self.tabs.setTabText(0, t("standard_tab"))
        self.tabs.setTabText(1, t("latex_tab"))
        self.tabs.setTabText(2, t("settings_tab"))

        self.setWindowTitle(t("app_title"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_dark_mode(CUSTOM_DICT.get("dark_mode", False))
    calc_app = CalculatorApp()
    calc_app.show()
    sys.exit(app.exec_())

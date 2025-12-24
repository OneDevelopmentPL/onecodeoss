# OneCode - OSS 
# Support me on Github (github.com/OneDevelopmentPL)
# Wesprzyj mnie na Github (github.com/OneDevelopmentPL)

# GitHub - https://github.com/OneDevelopmentPL/onecodeoss

import sys, os, re, subprocess, json
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from pygments.lexers import *
from pygments.token import Token
from pygments import lex

# ================== KONFIGURACJA ==================

class Config:
    """Zarządzanie konfiguracją edytora"""
    def __init__(self):
        self.config_path = Path.home() / ".onecode_config.json"
        self.settings = self.load()
    
    def load(self):
        defaults = {
            "theme": "dark",
            "font_size": 11,
            "font_family": "Consolas",
            "auto_save": True,
            "auto_save_interval": 30000,
            "show_minimap": True,
            "show_line_numbers": True,
            "tab_size": 4,
            "word_wrap": False,
            "recent_files": [],
            "recent_folders": []
        }
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except:
                pass
        return defaults
    
    def save(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

# ================== THEMES ==================

class Theme:
    DARK = {
        "bg": "#1E1E1E",
        "fg": "#D4D4D4",
        "selection": "#264F78",
        "current_line": "#2A2A2A",
        "sidebar": "#252526",
        "border": "#333333",
        "keyword": "#C586C0",
        "function": "#DCDCAA",
        "comment": "#6A9955",
        "string": "#CE9178",
        "number": "#B5CEA8",
        "operator": "#D4D4D4",
        "error": "#F48771",
        "warning": "#CCA700"
    }
    
    LIGHT = {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "selection": "#ADD6FF",
        "current_line": "#F0F0F0",
        "sidebar": "#F3F3F3",
        "border": "#E0E0E0",
        "keyword": "#0000FF",
        "function": "#795E26",
        "comment": "#008000",
        "string": "#A31515",
        "number": "#098658",
        "operator": "#000000",
        "error": "#E51400",
        "warning": "#BF8803"
    }

# ================== SYNTAX HIGHLIGHTER ==================

class AdvancedHighlighter(QSyntaxHighlighter):
    def __init__(self, document, lexer, theme):
        super().__init__(document)
        self.lexer = lexer
        self.theme = theme
        self.formats = {}
        self._init_formats()
    
    def _format(self, color, bold=False, italic=False):
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold: f.setFontWeight(QFont.Weight.Bold)
        if italic: f.setFontItalic(True)
        return f
    
    def _init_formats(self):
        self.formats[Token.Keyword] = self._format(self.theme["keyword"], True)
        self.formats[Token.Keyword.Namespace] = self._format(self.theme["keyword"], True)
        self.formats[Token.Name.Function] = self._format(self.theme["function"])
        self.formats[Token.Name.Class] = self._format(self.theme["function"], True)
        self.formats[Token.Comment] = self._format(self.theme["comment"], italic=True)
        self.formats[Token.Comment.Single] = self._format(self.theme["comment"], italic=True)
        self.formats[Token.Comment.Multiline] = self._format(self.theme["comment"], italic=True)
        self.formats[Token.String] = self._format(self.theme["string"])
        self.formats[Token.String.Double] = self._format(self.theme["string"])
        self.formats[Token.String.Single] = self._format(self.theme["string"])
        self.formats[Token.Number] = self._format(self.theme["number"])
        self.formats[Token.Number.Integer] = self._format(self.theme["number"])
        self.formats[Token.Number.Float] = self._format(self.theme["number"])
        self.formats[Token.Operator] = self._format(self.theme["operator"])
    
    def highlightBlock(self, text):
        if not self.lexer:
            return
        for token, content in lex(text, self.lexer):
            fmt = self.formats.get(token)
            if not fmt:
                # Sprawdź rodzica tokena
                parent = token
                while parent.parent and parent != parent.parent:
                    parent = parent.parent
                    if parent in self.formats:
                        fmt = self.formats[parent]
                        break
            if fmt:
                start = text.find(content)
                if start >= 0:
                    self.setFormat(start, len(content), fmt)

# ================== LINE NUMBERS ==================

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

# ================== MINIMAP ==================

class MiniMap(QPlainTextEdit):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMaximumWidth(120)
        self.setFont(QFont("Consolas", 2))
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        
    def update_minimap(self):
        self.setPlainText(self.editor.toPlainText())
        # Synchronizuj przewijanie
        ratio = self.editor.verticalScrollBar().value() / max(1, self.editor.verticalScrollBar().maximum())
        self.verticalScrollBar().setValue(int(ratio * self.verticalScrollBar().maximum()))

# ================== ADVANCED CODE EDITOR ==================

class AdvancedCodeEditor(QPlainTextEdit):
    def __init__(self, path=None, config=None, theme=None):
        super().__init__()
        self.path = path
        self.config = config or Config()
        self.theme = theme or Theme.DARK
        self.is_modified = False
        self.last_save_time = None
        
        # Setup
        self._setup_appearance()
        self._setup_line_numbers()
        self._init_autoclose()
        self._init_indentation()
        
        # Podświetlanie
        self.highlighter = None
        
        # Minimap
        self.minimap = None
        if self.config.settings.get("show_minimap", True):
            self.minimap = MiniMap(self)
        
        # Sygnały
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        
        # Search
        self.search_text = ""
        self.search_matches = []
        
    def _setup_appearance(self):
        font = QFont(
            self.config.settings.get("font_family", "Consolas"),
            self.config.settings.get("font_size", 11)
        )
        self.setFont(font)
        
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self.theme['bg']};
                color: {self.theme['fg']};
                border: none;
                selection-background-color: {self.theme['selection']};
            }}
        """)
        
        if self.config.settings.get("word_wrap", False):
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    
    def _setup_line_numbers(self):
        self.line_number_area = LineNumberArea(self)
        self.update_line_number_area_width(0)
    
    def _init_autoclose(self):
        self.auto_pairs = {
            "(": ")", "[": "]", "{": "}", "'": "'", '"': '"',
            "`": "`"
        }
    
    def _init_indentation(self):
        self.tab_size = self.config.settings.get("tab_size", 4)
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * self.tab_size)
    
    def _on_text_changed(self):
        self.is_modified = True
        if self.minimap:
            QTimer.singleShot(100, self.minimap.update_minimap)
    
    def _highlight_current_line(self):
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(self.theme["current_line"]))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        # Dodaj wyszukiwania
        for match in self.search_matches:
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#6A9955"))
            selection.cursor = self.textCursor()
            selection.cursor.setPosition(match[0])
            selection.cursor.setPosition(match[1], QTextCursor.MoveMode.KeepAnchor)
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def keyPressEvent(self, e):
        # Auto-zamykanie nawiasów
        key = e.text()
        cursor = self.textCursor()
        
        if key in self.auto_pairs and not cursor.hasSelection():
            closing = self.auto_pairs[key]
            cursor.insertText(key + closing)
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return
        
        # Inteligentne wcięcia
        if e.key() == Qt.Key.Key_Return:
            current_line = cursor.block().text()
            indent = len(current_line) - len(current_line.lstrip())
            super().keyPressEvent(e)
            
            # Dodaj wcięcie
            self.insertPlainText(" " * indent)
            
            # Jeśli linia kończy się ':' lub '{', dodaj dodatkowe wcięcie
            if current_line.rstrip().endswith((':','{')):
                self.insertPlainText(" " * self.tab_size)
            return
        
        # Tab jako spacje
        if e.key() == Qt.Key.Key_Tab:
            self.insertPlainText(" " * self.tab_size)
            return
        
        # Komentowanie linii (Ctrl+/)
        if e.key() == Qt.Key.Key_Slash and e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.toggle_comment()
            return
        
        # Duplikowanie linii (Ctrl+D)
        if e.key() == Qt.Key.Key_D and e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.duplicate_line()
            return
        
        # Usuwanie linii (Ctrl+Shift+K)
        if e.key() == Qt.Key.Key_K and e.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.delete_line()
            return
        
        super().keyPressEvent(e)
    
    def toggle_comment(self):
        """Komentowanie/odkomentowanie linii"""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        # Pobierz comment prefix dla języka
        comment = "//" if self.path and any(self.path.endswith(x) for x in ['.cpp', '.js', '.c']) else "#"
        
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        
        while cursor.position() <= end:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            line = cursor.block().text()
            
            if line.strip().startswith(comment):
                # Usuń komentarz
                pos = line.index(comment)
                cursor.setPosition(cursor.block().position() + pos)
                cursor.deleteChar()
                if comment == "//":
                    cursor.deleteChar()
            else:
                # Dodaj komentarz
                cursor.insertText(comment + " ")
            
            if not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                break
        
        cursor.endEditBlock()
    
    def duplicate_line(self):
        """Duplikuj aktualną linię"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        text = cursor.selectedText()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertText("\n" + text)
    
    def delete_line(self):
        """Usuń aktualną linię"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deleteChar()  # Usuń newline
    
    def search(self, text, case_sensitive=False):
        """Wyszukaj tekst w edytorze"""
        self.search_text = text
        self.search_matches = []
        
        if not text:
            self._highlight_current_line()
            return
        
        content = self.toPlainText()
        if not case_sensitive:
            text = text.lower()
            content = content.lower()
        
        start = 0
        while True:
            pos = content.find(text, start)
            if pos == -1:
                break
            self.search_matches.append((pos, pos + len(text)))
            start = pos + 1
        
        self._highlight_current_line()
    
    # Line numbers
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits
    
    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    
    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.theme["sidebar"]))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        current_line = self.textCursor().blockNumber()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number == current_line:
                    painter.setPen(QColor(self.theme["fg"]))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor("#858585"))
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
                
                painter.drawText(0, top, self.line_number_area.width() - 5, 
                               self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

# ================== STATUS BAR ==================

class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.line_col_label = QLabel("Ln 1, Col 1")
        self.encoding_label = QLabel("UTF-8")
        self.lang_label = QLabel("Plain Text")
        self.addPermanentWidget(self.line_col_label)
        self.addPermanentWidget(self.encoding_label)
        self.addPermanentWidget(self.lang_label)
    
    def update_position(self, line, col):
        self.line_col_label.setText(f"Ln {line}, Col {col}")
    
    def update_language(self, lang):
        self.lang_label.setText(lang)

# ================== SEARCH WIDGET ==================

class SearchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj...")
        
        self.case_btn = QPushButton("Aa")
        self.case_btn.setCheckable(True)
        self.case_btn.setMaximumWidth(40)
        
        self.prev_btn = QPushButton("◄")
        self.prev_btn.setMaximumWidth(30)
        
        self.next_btn = QPushButton("►")
        self.next_btn.setMaximumWidth(30)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setMaximumWidth(30)
        
        layout.addWidget(QLabel("🔍"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.case_btn)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        self.hide()

# ================== MAIN WINDOW ==================

class OneCodePro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.theme = Theme.DARK if self.config.settings["theme"] == "dark" else Theme.LIGHT
        
        self.setWindowTitle("OneCode - OSS")
        self.resize(1400, 900)
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        if self.config.settings.get("auto_save", True):
            self.auto_save_timer.start(self.config.settings.get("auto_save_interval", 30000))
        
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()
        
        # Przywróć ostatnie pliki
        self._restore_recent_files()
    
    def _setup_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # Sidebar
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # File tree
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.currentPath()))
        self.tree.setHeaderHidden(True)
        for i in range(1, 4):
            self.tree.hideColumn(i)
        self.tree.doubleClicked.connect(self._open_selected_file)
        
        # Folder selector
        folder_btn = QPushButton("📁 Otwórz folder")
        folder_btn.clicked.connect(self._select_folder)
        
        sidebar_layout.addWidget(folder_btn)
        sidebar_layout.addWidget(self.tree)
        sidebar.setLayout(sidebar_layout)
        
        main_splitter.addWidget(sidebar)
        
        # Editor area
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search widget
        self.search_widget = SearchWidget()
        self.search_widget.close_btn.clicked.connect(lambda: self.search_widget.hide())
        self.search_widget.search_input.textChanged.connect(self._perform_search)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        
        editor_layout.addWidget(self.search_widget)
        editor_layout.addWidget(self.tabs)
        editor_widget.setLayout(editor_layout)
        
        # Terminal
        self.terminal_widget = self._create_terminal()
        
        # Vertical splitter
        vsplitter = QSplitter(Qt.Orientation.Vertical)
        vsplitter.addWidget(editor_widget)
        vsplitter.addWidget(self.terminal_widget)
        vsplitter.setSizes([600, 200])
        
        main_splitter.addWidget(vsplitter)
        main_splitter.setSizes([200, 1000])
    
    def _create_terminal(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Terminal output
        self.terminal_view = QPlainTextEdit()
        self.terminal_view.setReadOnly(True)
        self.terminal_view.setFont(QFont("Consolas", 10))
        
        # Terminal input
        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Wpisz komendę...")
        self.terminal_input.returnPressed.connect(self._exec_terminal_command)
        
        # Terminal process
        self.terminal_process = QProcess()
        shell = "bash" if os.name != "nt" else "cmd"
        self.terminal_process.start(shell)
        self.terminal_process.readyReadStandardOutput.connect(self._terminal_output)
        self.terminal_process.readyReadStandardError.connect(self._terminal_error)
        
        layout.addWidget(self.terminal_view)
        layout.addWidget(self.terminal_input)
        widget.setLayout(layout)
        
        return widget
    
    def _setup_menu(self):
        menubar = self.menuBar()
        
        # Plik
        file_menu = menubar.addMenu("📁 Plik")
        
        new_act = QAction("Nowy plik", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self._new_file)
        
        open_act = QAction("Otwórz plik", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_file_dialog)
        
        save_act = QAction("Zapisz", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._save_file)
        
        save_as_act = QAction("Zapisz jako...", self)
        save_as_act.setShortcut("Ctrl+Shift+S")
        save_as_act.triggered.connect(self._save_file_as)
        
        save_all_act = QAction("Zapisz wszystko", self)
        save_all_act.setShortcut("Ctrl+Alt+S")
        save_all_act.triggered.connect(self._save_all)
        
        close_act = QAction("Zamknij", self)
        close_act.setShortcut("Ctrl+W")
        close_act.triggered.connect(lambda: self._close_tab(self.tabs.currentIndex()))
        
        file_menu.addActions([new_act, open_act, save_act, save_as_act, save_all_act, close_act])
        
        # Edycja
        edit_menu = menubar.addMenu("✏️ Edycja")
        
        undo_act = QAction("Cofnij", self)
        undo_act.setShortcut("Ctrl+Z")
        undo_act.triggered.connect(self._undo)
        
        redo_act = QAction("Ponów", self)
        redo_act.setShortcut("Ctrl+Y")
        redo_act.triggered.connect(self._redo)
        
        find_act = QAction("Znajdź", self)
        find_act.setShortcut("Ctrl+F")
        find_act.triggered.connect(self._show_search)
        
        replace_act = QAction("Zamień", self)
        replace_act.setShortcut("Ctrl+H")
        replace_act.triggered.connect(self._show_replace)
        
        edit_menu.addActions([undo_act, redo_act, find_act, replace_act])
        
        # Widok
        view_menu = menubar.addMenu("👁️ Widok")
        
        theme_act = QAction("Zmień motyw", self)
        theme_act.triggered.connect(self._toggle_theme)
        
        minimap_act = QAction("Pokaż minimap", self)
        minimap_act.setCheckable(True)
        minimap_act.setChecked(self.config.settings.get("show_minimap", True))
        minimap_act.triggered.connect(self._toggle_minimap)
        
        wrap_act = QAction("Zawijanie wierszy", self)
        wrap_act.setCheckable(True)
        wrap_act.setChecked(self.config.settings.get("word_wrap", False))
        wrap_act.triggered.connect(self._toggle_word_wrap)
        
        view_menu.addActions([theme_act, minimap_act, wrap_act])
        
        # Uruchom
        run_menu = menubar.addMenu("▶️ Uruchom")
        
        run_act = QAction("Uruchom plik", self)
        run_act.setShortcut("F5")
        run_act.triggered.connect(self._run_file)
        
        run_menu.addAction(run_act)
        
        # Pomoc
        help_menu = menubar.addMenu("❓ Pomoc")
        
        about_act = QAction("O programie", self)
        about_act.triggered.connect(self._show_about)
        
        shortcuts_act = QAction("Skróty klawiszowe", self)
        shortcuts_act.triggered.connect(self._show_shortcuts)
        
        help_menu.addActions([about_act, shortcuts_act])
    
    def _setup_toolbar(self):
        toolbar = QToolBar("Główne")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        
        new_btn = QAction("📝", self)
        new_btn.setToolTip("Nowy plik (Ctrl+N)")
        new_btn.triggered.connect(self._new_file)
        
        open_btn = QAction("📂", self)
        open_btn.setToolTip("Otwórz (Ctrl+O)")
        open_btn.triggered.connect(self._open_file_dialog)
        
        save_btn = QAction("💾", self)
        save_btn.setToolTip("Zapisz (Ctrl+S)")
        save_btn.triggered.connect(self._save_file)
        
        run_btn = QAction("▶️", self)
        run_btn.setToolTip("Uruchom (F5)")
        run_btn.triggered.connect(self._run_file)
        
        search_btn = QAction("🔍", self)
        search_btn.setToolTip("Szukaj (Ctrl+F)")
        search_btn.triggered.connect(self._show_search)
        
        toolbar.addActions([new_btn, open_btn, save_btn, run_btn, search_btn])
    
    def _setup_statusbar(self):
        self.status = StatusBar()
        self.setStatusBar(self.status)
    
    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.theme['bg']};
                color: {self.theme['fg']};
            }}
            QMenuBar {{
                background: {self.theme['sidebar']};
                color: {self.theme['fg']};
                padding: 3px;
            }}
            QMenuBar::item:selected {{
                background: {self.theme['selection']};
            }}
            QMenu {{
                background: {self.theme['sidebar']};
                color: {self.theme['fg']};
                border: 1px solid {self.theme['border']};
            }}
            QMenu::item:selected {{
                background: {self.theme['selection']};
            }}
            QToolBar {{
                background: {self.theme['sidebar']};
                border: none;
                spacing: 5px;
                padding: 5px;
            }}
            QTreeView {{
                background-color: {self.theme['sidebar']};
                color: {self.theme['fg']};
                border: none;
            }}
            QTreeView::item:hover {{
                background: {self.theme['current_line']};
            }}
            QTreeView::item:selected {{
                background: {self.theme['selection']};
            }}
            QTabWidget::pane {{
                border: none;
            }}
            QTabBar::tab {{
                background: {self.theme['sidebar']};
                color: {self.theme['fg']};
                padding: 8px 15px;
                border: none;
            }}
            QTabBar::tab:selected {{
                background: {self.theme['bg']};
                border-bottom: 2px solid {self.theme['keyword']};
            }}
            QTabBar::tab:hover {{
                background: {self.theme['current_line']};
            }}
            QPlainTextEdit {{
                background-color: {self.theme['bg']};
                color: {self.theme['fg']};
                border: none;
            }}
            QLineEdit {{
                background-color: {self.theme['sidebar']};
                color: {self.theme['fg']};
                border: 1px solid {self.theme['border']};
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {self.theme['sidebar']};
                color: {self.theme['fg']};
                border: 1px solid {self.theme['border']};
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['current_line']};
            }}
            QPushButton:pressed {{
                background-color: {self.theme['selection']};
            }}
            QStatusBar {{
                background: {self.theme['sidebar']};
                color: {self.theme['fg']};
            }}
        """)
        
        self.tree.setStyleSheet(f"background-color:{self.theme['sidebar']};color:{self.theme['fg']};")
        self.terminal_view.setStyleSheet(f"background-color:{self.theme['bg']};color:{self.theme['fg']};")
        self.terminal_input.setStyleSheet(f"background-color:{self.theme['sidebar']};color:{self.theme['fg']};")
    
    # ========== FILE OPERATIONS ==========
    
    def _new_file(self):
        editor = AdvancedCodeEditor(None, self.config, self.theme)
        self._add_editor_tab(editor, "Nowy plik")
    
    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Otwórz plik", "", 
            "Wszystkie pliki (*.*);;Python (*.py);;C++ (*.cpp);;HTML (*.html);;CSS (*.css);;JavaScript (*.js)"
        )
        if path:
            self._open_file(path)
    
    def _open_selected_file(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self._open_file(path)
    
    def _open_file(self, path):
        # Sprawdź czy plik jest już otwarty
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor and editor.path == path:
                self.tabs.setCurrentIndex(i)
                return
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie można otworzyć pliku:\n{str(e)}")
            return
        
        editor = AdvancedCodeEditor(path, self.config, self.theme)
        editor.setPlainText(text)
        editor.is_modified = False
        
        # Setup highlighter
        lexer = self._get_lexer(path)
        if lexer:
            editor.highlighter = AdvancedHighlighter(editor.document(), lexer, self.theme)
        
        self._add_editor_tab(editor, os.path.basename(path))
        
        # Dodaj do ostatnio otwartych
        self._add_to_recent(path)
        
        self.status.showMessage(f"Otwarto: {path}", 3000)
    
    def _add_editor_tab(self, editor, title):
        # Create container with editor and minimap
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(editor)
        
        if editor.minimap:
            layout.addWidget(editor.minimap)
            editor.textChanged.connect(editor.minimap.update_minimap)
            editor.minimap.update_minimap()
        
        container.setLayout(layout)
        
        idx = self.tabs.addTab(container, title)
        self.tabs.setCurrentIndex(idx)
        
        # Connect cursor position updates
        editor.cursorPositionChanged.connect(lambda: self._update_cursor_position(editor))
    
    def _save_file(self):
        if self.tabs.count() == 0:
            return
        
        editor = self._get_current_editor()
        if not editor:
            return
        
        if not editor.path:
            self._save_file_as()
            return
        
        try:
            with open(editor.path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            editor.is_modified = False
            editor.last_save_time = QTimer()
            self._update_tab_title(self.tabs.currentIndex())
            self.status.showMessage(f"Zapisano: {editor.path}", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Błąd", f"Nie można zapisać pliku:\n{str(e)}")
    
    def _save_file_as(self):
        editor = self._get_current_editor()
        if not editor:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz jako", "", "Wszystkie pliki (*.*)"
        )
        
        if path:
            editor.path = path
            self._save_file()
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
            
            # Update highlighter
            lexer = self._get_lexer(path)
            if lexer:
                editor.highlighter = AdvancedHighlighter(editor.document(), lexer, self.theme)
            
            self._add_to_recent(path)
    
    def _save_all(self):
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor and editor.is_modified:
                if editor.path:
                    try:
                        with open(editor.path, 'w', encoding='utf-8') as f:
                            f.write(editor.toPlainText())
                        editor.is_modified = False
                        self._update_tab_title(i)
                    except:
                        pass
        self.status.showMessage("Zapisano wszystkie pliki", 3000)
    
    def _auto_save(self):
        """Auto-zapisywanie plików"""
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor and editor.is_modified and editor.path:
                try:
                    with open(editor.path, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    editor.is_modified = False
                except:
                    pass
    
    def _close_tab(self, index):
        if index < 0:
            return
        
        widget = self.tabs.widget(index)
        editor = widget.findChild(AdvancedCodeEditor)
        
        if editor and editor.is_modified:
            reply = QMessageBox.question(
                self, "Niezapisane zmiany",
                f"Czy chcesz zapisać zmiany w {self.tabs.tabText(index)}?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        self.tabs.removeTab(index)
    
    def _update_tab_title(self, index):
        widget = self.tabs.widget(index)
        editor = widget.findChild(AdvancedCodeEditor)
        if editor:
            title = os.path.basename(editor.path) if editor.path else "Nowy plik"
            if editor.is_modified:
                title = "● " + title
            self.tabs.setTabText(index, title)
    
    # ========== EDITOR OPERATIONS ==========
    
    def _undo(self):
        editor = self._get_current_editor()
        if editor:
            editor.undo()
    
    def _redo(self):
        editor = self._get_current_editor()
        if editor:
            editor.redo()
    
    def _show_search(self):
        self.search_widget.show()
        self.search_widget.search_input.setFocus()
    
    def _show_replace(self):
        # TODO: Implement replace dialog
        self._show_search()
    
    def _perform_search(self):
        editor = self._get_current_editor()
        if editor:
            text = self.search_widget.search_input.text()
            case_sensitive = self.search_widget.case_btn.isChecked()
            editor.search(text, case_sensitive)
    
    # ========== VIEW OPERATIONS ==========
    
    def _toggle_theme(self):
        if self.config.settings["theme"] == "dark":
            self.config.settings["theme"] = "light"
            self.theme = Theme.LIGHT
        else:
            self.config.settings["theme"] = "dark"
            self.theme = Theme.DARK
        
        self.config.save()
        self._apply_theme()
        
        # Update all editors
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor:
                editor.theme = self.theme
                editor._setup_appearance()
                if editor.highlighter:
                    editor.highlighter.theme = self.theme
                    editor.highlighter._init_formats()
                    editor.highlighter.rehighlight()
    
    def _toggle_minimap(self):
        show = not self.config.settings.get("show_minimap", True)
        self.config.settings["show_minimap"] = show
        self.config.save()
        QMessageBox.information(self, "Minimap", 
            "Zmiana zostanie zastosowana dla nowych plików.\nZamknij i otwórz ponownie istniejące pliki.")
    
    def _toggle_word_wrap(self):
        wrap = not self.config.settings.get("word_wrap", False)
        self.config.settings["word_wrap"] = wrap
        self.config.save()
        
        # Apply to all open editors
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor:
                if wrap:
                    editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
                else:
                    editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    
    # ========== RUN OPERATIONS ==========
    
    def _run_file(self):
        editor = self._get_current_editor()
        if not editor or not editor.path:
            QMessageBox.warning(self, "Uwaga", "Najpierw zapisz plik.")
            return
        
        self._save_file()
        
        ext = os.path.splitext(editor.path)[1].lower()
        
        commands = {
            ".py": f"python \"{editor.path}\"",
            ".cpp": f"g++ \"{editor.path}\" -o temp.exe && temp.exe" if os.name == "nt" else f"g++ \"{editor.path}\" -o temp.out && ./temp.out",
            ".c": f"gcc \"{editor.path}\" -o temp.exe && temp.exe" if os.name == "nt" else f"gcc \"{editor.path}\" -o temp.out && ./temp.out",
            ".js": f"node \"{editor.path}\"",
            ".html": f"start \"{editor.path}\"" if os.name == "nt" else f"xdg-open \"{editor.path}\"",
            ".java": f"javac \"{editor.path}\" && java {os.path.splitext(os.path.basename(editor.path))[0]}"
        }
        
        cmd = commands.get(ext)
        
        if cmd:
            self.terminal_view.appendPlainText(f"\n> {cmd}\n")
            self.terminal_process.write((cmd + "\n").encode())
            self.status.showMessage(f"Uruchomiono: {os.path.basename(editor.path)}", 3000)
        else:
            QMessageBox.information(self, "Uwaga", 
                f"Nieobsługiwane rozszerzenie: {ext}\n\n"
                "Obsługiwane: .py, .cpp, .c, .js, .html, .java")
    
    # ========== TERMINAL ==========
    
    def _terminal_output(self):
        data = self.terminal_process.readAllStandardOutput().data().decode(errors='ignore')
        self.terminal_view.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal_view.insertPlainText(data)
        self.terminal_view.moveCursor(QTextCursor.MoveOperation.End)
    
    def _terminal_error(self):
        data = self.terminal_process.readAllStandardError().data().decode(errors='ignore')
        self.terminal_view.moveCursor(QTextCursor.MoveOperation.End)
        cursor = self.terminal_view.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.theme["error"]))
        cursor.setCharFormat(fmt)
        cursor.insertText(data)
        self.terminal_view.setTextCursor(cursor)
    
    def _exec_terminal_command(self):
        cmd = self.terminal_input.text().strip()
        if not cmd:
            return
        
        self.terminal_view.appendPlainText(f"> {cmd}")
        self.terminal_process.write((cmd + "\n").encode())
        self.terminal_input.clear()
    
    # ========== UTILITIES ==========
    
    def _get_current_editor(self):
        if self.tabs.count() == 0:
            return None
        widget = self.tabs.currentWidget()
        return widget.findChild(AdvancedCodeEditor) if widget else None
    
    def _get_lexer(self, path):
        ext = os.path.splitext(path)[1].lower()
        lexers = {
            ".py": PythonLexer(),
            ".cpp": CppLexer(),
            ".c": CppLexer(),
            ".h": CppLexer(),
            ".hpp": CppLexer(),
            ".html": HtmlLexer(),
            ".htm": HtmlLexer(),
            ".css": CssLexer(),
            ".js": JavascriptLexer(),
            ".json": JavascriptLexer(),
            ".java": get_lexer_by_name('java'),
            ".php": get_lexer_by_name('php'),
            ".rb": get_lexer_by_name('ruby'),
            ".go": get_lexer_by_name('go'),
            ".rs": get_lexer_by_name('rust'),
            ".ts": get_lexer_by_name('typescript'),
            ".sql": get_lexer_by_name('sql'),
            ".sh": get_lexer_by_name('bash'),
            ".bat": get_lexer_by_name('batch'),
            ".xml": get_lexer_by_name('xml'),
            ".yaml": get_lexer_by_name('yaml'),
            ".yml": get_lexer_by_name('yaml'),
            ".md": get_lexer_by_name('markdown'),
        }
        return lexers.get(ext)
    
    def _update_cursor_position(self, editor):
        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.status.update_position(line, col)
        
        # Update language in status bar
        if editor.path:
            ext = os.path.splitext(editor.path)[1].upper()[1:]
            self.status.update_language(ext if ext else "Plain Text")
    
    def _tab_changed(self, index):
        if index >= 0:
            widget = self.tabs.widget(index)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor:
                self._update_cursor_position(editor)
    
    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder")
        if folder:
            self.model.setRootPath(folder)
            self.tree.setRootIndex(self.model.index(folder))
            self.config.settings.setdefault("recent_folders", [])
            if folder not in self.config.settings["recent_folders"]:
                self.config.settings["recent_folders"].insert(0, folder)
                self.config.settings["recent_folders"] = self.config.settings["recent_folders"][:10]
                self.config.save()
    
    def _add_to_recent(self, path):
        self.config.settings.setdefault("recent_files", [])
        if path in self.config.settings["recent_files"]:
            self.config.settings["recent_files"].remove(path)
        self.config.settings["recent_files"].insert(0, path)
        self.config.settings["recent_files"] = self.config.settings["recent_files"][:20]
        self.config.save()
    
    def _restore_recent_files(self):
        # Możesz tutaj dodać menu z ostatnimi plikami
        pass
    
    def _show_about(self):
        QMessageBox.about(self, "OneCode - OSS", 
            "<h2>OneCode - OSS</h2>"
            "<p>Zaawansowany edytor kodu inspirowany Visual Studio Code</p>"
            "<p><b>Funkcje:</b></p>"
            "<ul>"
            "<li>Podświetlanie składni dla wielu języków</li>"
            "<li>Numeracja linii i minimap</li>"
            "<li>Auto-uzupełnianie i auto-zamykanie nawiasów</li>"
            "<li>Inteligentne wcięcia</li>"
            "<li>Wbudowany terminal</li>"
            "<li>Wyszukiwanie i zamiana</li>"
            "<li>Auto-zapisywanie</li>"
            "<li>Motywy jasny/ciemny</li>"
            "<li>Uruchamianie kodu</li>"
            "</ul>"
            "<p>Made with ❤️ using PySide6</p>")
    
    def _show_shortcuts(self):
        QMessageBox.information(self, "Skróty klawiszowe",
            "<h3>Skróty klawiszowe</h3>"
            "<table>"
            "<tr><td><b>Ctrl+N</b></td><td>Nowy plik</td></tr>"
            "<tr><td><b>Ctrl+O</b></td><td>Otwórz plik</td></tr>"
            "<tr><td><b>Ctrl+S</b></td><td>Zapisz</td></tr>"
            "<tr><td><b>Ctrl+Shift+S</b></td><td>Zapisz jako</td></tr>"
            "<tr><td><b>Ctrl+W</b></td><td>Zamknij zakładkę</td></tr>"
            "<tr><td><b>Ctrl+F</b></td><td>Szukaj</td></tr>"
            "<tr><td><b>Ctrl+H</b></td><td>Zamień</td></tr>"
            "<tr><td><b>Ctrl+Z</b></td><td>Cofnij</td></tr>"
            "<tr><td><b>Ctrl+Y</b></td><td>Ponów</td></tr>"
            "<tr><td><b>Ctrl+/</b></td><td>Komentarz</td></tr>"
            "<tr><td><b>Ctrl+D</b></td><td>Duplikuj linię</td></tr>"
            "<tr><td><b>Ctrl+Shift+K</b></td><td>Usuń linię</td></tr>"
            "<tr><td><b>F5</b></td><td>Uruchom</td></tr>"
            "</table>")
    
    def closeEvent(self, event):
        # Sprawdź niezapisane pliki
        modified = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            editor = widget.findChild(AdvancedCodeEditor)
            if editor and editor.is_modified:
                modified.append(self.tabs.tabText(i))
        
        if modified:
            reply = QMessageBox.question(
                self, "Niezapisane zmiany",
                f"Masz {len(modified)} niezapisanych plików. Czy chcesz zapisać wszystkie?",
                QMessageBox.StandardButton.SaveAll | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.SaveAll:
                self._save_all()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        # Zakończ proces terminala
        self.terminal_process.kill()
        event.accept()

# ================== MAIN ==================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OneCode - OSS")
    app.setOrganizationName("OneDevelopment")
    
    window = OneCodePro()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
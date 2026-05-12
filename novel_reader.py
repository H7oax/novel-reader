import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QMessageBox, QMenu, QAction, QColorDialog
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QVBoxLayout, QWidget

# 尝试导入不同格式支持库
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

try:
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    epub = None
    BeautifulSoup = None


class TransparentReader(QMainWindow):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.initUI(text)

    def initUI(self, text):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(100, 100, 600, 400)

        central = QWidget(self)
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #333333;
                font-size: 16px;
            }
        """)
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.text_edit)

        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)
        self.drag_pos = QPoint()

    def show_context_menu(self, pos):
        menu = QMenu()
        enlarge_action = QAction("放大字体", self)
        shrink_action = QAction("缩小字体", self)
        change_color_action = QAction("更改文字颜色", self)
        close_action = QAction("退出", self)

        enlarge_action.triggered.connect(self.increase_font)
        shrink_action.triggered.connect(self.decrease_font)
        change_color_action.triggered.connect(self.change_text_color)
        close_action.triggered.connect(self.close)

        menu.addAction(enlarge_action)
        menu.addAction(shrink_action)
        menu.addAction(change_color_action)
        menu.addSeparator()
        menu.addAction(close_action)
        menu.exec_(self.text_edit.mapToGlobal(pos))

    def increase_font(self):
        font = self.text_edit.font()
        font.setPointSize(font.pointSize() + 2)
        self.text_edit.setFont(font)

    def decrease_font(self):
        font = self.text_edit.font()
        if font.pointSize() > 6:
            font.setPointSize(font.pointSize() - 2)
            self.text_edit.setFont(font)

    def change_text_color(self):
        color = QColorDialog.getColor(initial=QColor("#333333"), parent=self, title="选择文字颜色")
        if color.isValid():
            font_size = self.text_edit.font().pointSize()
            self.text_edit.setStyleSheet(f"""
                QTextEdit {{
                    background: transparent;
                    border: none;
                    color: {color.name()};
                    font-size: {font_size}px;
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()


class NormalReader(QMainWindow):
    def __init__(self, text):
        super().__init__()
        self.setWindowTitle("小说阅读器（普通模式）")
        self.setGeometry(200, 200, 700, 500)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("font-size: 16px;")
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu()
        enlarge_action = QAction("放大字体", self)
        shrink_action = QAction("缩小字体", self)
        close_action = QAction("关闭", self)

        enlarge_action.triggered.connect(self.increase_font)
        shrink_action.triggered.connect(self.decrease_font)
        close_action.triggered.connect(self.close)

        menu.addAction(enlarge_action)
        menu.addAction(shrink_action)
        menu.addSeparator()
        menu.addAction(close_action)
        menu.exec_(self.text_edit.mapToGlobal(pos))

    def increase_font(self):
        font = self.text_edit.font()
        font.setPointSize(font.pointSize() + 2)
        self.text_edit.setFont(font)

    def decrease_font(self):
        font = self.text_edit.font()
        if font.pointSize() > 6:
            font.setPointSize(font.pointSize() - 2)
            self.text_edit.setFont(font)


def extract_text(file_path):
    """根据后缀提取文本，支持 TXT, PDF, DOCX, EPUB"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    elif ext == '.pdf':
        if pdfplumber is None:
            QMessageBox.critical(None, "错误", "缺少 pdfplumber 库，请运行：pip install pdfplumber")
            return None
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            QMessageBox.critical(None, "提取错误", f"PDF 读取失败：{e}")
            return None

    elif ext == '.docx':
        if docx is None:
            QMessageBox.critical(None, "错误", "缺少 python-docx 库，请运行：pip install python-docx")
            return None
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            QMessageBox.critical(None, "提取错误", f"DOCX 读取失败：{e}")
            return None

    elif ext == '.epub':
        if epub is None or BeautifulSoup is None:
            QMessageBox.critical(None, "错误", "缺少 ebooklib 和 beautifulsoup4，请运行：pip install ebooklib beautifulsoup4")
            return None
        try:
            book = epub.read_epub(file_path)
            texts = []
            for item in book.get_items_of_type(9):  # ITEM_DOCUMENT
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                texts.append(soup.get_text())
            return "\n".join(texts)
        except Exception as e:
            QMessageBox.critical(None, "提取错误", f"EPUB 读取失败：{e}")
            return None

    else:
        QMessageBox.warning(None, "格式暂不支持", "目前支持：TXT, PDF, DOCX, EPUB")
        return None


def main():
    app = QApplication(sys.argv)

    file_path, _ = QFileDialog.getOpenFileName(
        None, "选择小说文件", "",
        "电子书文件 (*.txt *.pdf *.docx *.epub);;所有文件 (*)"
    )
    if not file_path:
        sys.exit(0)

    text = extract_text(file_path)
    if text is None or len(text.strip()) == 0:
        QMessageBox.warning(None, "提示", "文件内容为空或无法提取。")
        sys.exit(0)

    reply = QMessageBox.question(
        None, "阅读模式",
        "您希望使用透明模式（上班隐蔽阅读）吗？\n\n"
        "选择“是”：窗口透明，只显示文字。\n"
        "选择“否”：普通窗口模式。",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
    )

    if reply == QMessageBox.Yes:
        window = TransparentReader(text)
    else:
        window = NormalReader(text)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

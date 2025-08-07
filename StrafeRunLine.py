import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt


class TransparentLineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 始终置顶
            Qt.Tool  # 不显示在任务栏
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 鼠标事件穿透

        # 线条样式属性
        self.line_color = QColor(255, 0, 0)  # 红色线条
        self.line_width = 3

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 设置画笔
        pen = QPen(self.line_color, self.line_width)
        painter.setPen(pen)

        # 绘制垂直线(居左)
        width = self.width()
        height = self.height()
        painter.drawLine(0, 0, 0, height)


class StrafeLine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Left Strafe Line')
        self.setGeometry(100, 100, 400, 400)

        # 创建透明线窗口
        self.line_window = TransparentLineWidget()
        self.reAdjustLines()
        self.color_dict = {
            "Green": QColor(0, 255, 0),  # 绿色
            "Red": QColor(255, 0, 0),  # 红色
            "Blue": QColor(0, 0, 255),  # 蓝色
            "Black": QColor(0, 0, 0),  # 黑色
            "Brown": QColor(165, 42, 42),  # 棕色
            "White": QColor(255, 255, 255),  # 白色
            "Yellow": QColor(255, 255, 0),  # 黄色
            "Orange": QColor(255, 165, 0),  # 橙色
            "Purple": QColor(128, 0, 128),  # 紫色
            "Teal": QColor(0, 128, 128)  # 凫蓝/水鸭色
        }

    def show_line(self):
        self.line_window.show()

    def hide_line(self):
        self.line_window.hide()

    def set_width(self,width:int):
        self.line_window.line_width=width
        self.line_window.update()

    def set_color(self, color: str):
        if color in self.color_dict:
            self.line_window.line_color = self.color_dict[color]
            self.line_window.update()
        else:
            print(f"未知颜色: {color}")

    def reAdjustLines(self):
        rect = self.geometry()
        self.line_window.setGeometry(
            rect.x(), rect.y(), rect.width(), rect.height()
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StrafeLine()
    window.show_line()
    sys.exit(app.exec_())
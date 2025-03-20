import nuke
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QKeyEvent
from PySide2.QtCore import Qt, QObject

class NukeKeyListener(QObject):  # Inherit from QObject
    def __init__(self):
        super().__init__()  # Initialize QObject
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        self.app.installEventFilter(self)

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent):
            if event.type() == QKeyEvent.KeyPress:
                if event.key() == Qt.Key_Right:
                    self.move_node_right()
                elif event.key() == Qt.Key_Left:
                    self.move_node_left()
        return super().eventFilter(obj, event)  # Call parent method to maintain functionality

    def move_node_right(self):
        node = nuke.selectedNode()
        if node:
            xpos = node['xpos'].value()
            node['xpos'].setValue(xpos + 10)
            print(f"Moved {node.name()} to xpos {xpos + 10}")

    def move_node_left(self):
        node = nuke.selectedNode()
        if node:
            xpos = node['xpos'].value()
            node['xpos'].setValue(xpos - 10)
            print(f"Moved {node.name()} to xpos {xpos + 10}")
# Initialize listener
key_listener = NukeKeyListener()

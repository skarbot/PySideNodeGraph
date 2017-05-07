#!/usr/bin/python
import sys

from PySide import QtGui, QtCore

from pySideNodeGraph import NodeItem
from pySideNodeGraph import NodeScene, NodeViewer


class TestNode(NodeItem):

    def __init__(self, name='Node', parent=None):
        super(TestNode, self).__init__(name, parent)
        self.add_input_port(label='input 1')
        self.add_input_port(label='input 2')
        self.add_input_port(label='input 3')
        self.add_input_port(label='input 4')

        self.add_output_port(label='output 1')
        self.add_output_port(label='output 2')
        self.add_output_port(label='output 3')


class NodeGraph(QtGui.QWidget):

    def __init__(self, parent=None):
        super(NodeGraph, self).__init__(parent)
        self.setWindowTitle('PySide Node Graph')
        self.nodeScene = NodeScene(self)
        self.nodeViewer = NodeViewer(self.nodeScene, self)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.nodeViewer)

        self.addNode(TestNode('My Node 1'), -500, 0)
        self.addNode(TestNode('My Node 2'), -500, -150)
        self.addNode(TestNode('My Node 3'), -800, -150)
        self.addNode(TestNode('My Node 4'), -800, 0)

    def addNode(self, node, xpos=0, ypos=0):
        assert isinstance(node, NodeItem), 'node must be a NodeItem'
        node.setPos(xpos, ypos)
        self.nodeScene.addItem(node)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    editor = NodeGraph()
    editor.show()
    editor.resize(850, 550)
    app.exec_()

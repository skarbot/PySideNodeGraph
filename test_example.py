#!/usr/bin/python
import sys

from PySide import QtGui

from pySideNodeGraph import NodeItem
from pySideNodeGraph import NodeScene, NodeViewer


class TestNode(NodeItem):

    def __init__(self, name='Foo Bar', parent=None):
        super(TestNode, self).__init__(name, parent)
        self.addInputPort(label='one only', connectionLimit=1)
        self.addInputPort(label='limit 2', connectionLimit=2)
        self.addInputPort(label='test')

        self.addOutputPort(label='hello')
        self.addOutputPort(label='world')
        self.addOutputPort(label='test')


class NodeGraph(QtGui.QWidget):

    def __init__(self, parent=None):
        super(NodeGraph, self).__init__(parent)
        self.setWindowTitle('Noodle Graph')
        self.nodeScene = NodeScene(self)
        self.nodeViewer = NodeViewer(self.nodeScene, self)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.nodeViewer)

        self.addNode(TestNode(), -50, 0)
        self.addNode(TestNode(), 150, -200)
        self.addNode(TestNode(), 200, 100)

    def addNode(self, node, xpos=0, ypos=0):
        assert isinstance(node, NodeItem), 'node must be a NodeItem'
        node.setPos(xpos, ypos)
        self.nodeScene.addItem(node)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    editor = NodeGraph()
    editor.show()
    editor.resize(850, 550)
    app.exec_()

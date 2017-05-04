#!/usr/bin/python
from PySide import QtGui, QtCore


class PipeItem(QtGui.QGraphicsPathItem):

    def __init__(self, color='#C28D34', dottedColor='#4A596C'):
        super(PipeItem, self).__init__(None)
        self.setFlag(self.ItemIsSelectable, False)
        self._color = color
        self._dottedColor = dottedColor
        self._inPort = None
        self._outPort = None
        self.setDottedLine(False)

    def __str__(self):
        return 'PipeItem(color={}, dottedColor={})'.format(self._color, self._colorGhost)

    def setColor(self, color):
        self._color = color
        self.setDottedLine()

    def setDottedLine(self, mode=False):
        penType = {
            True: QtCore.Qt.PenStyle.DashDotDotLine,
            False: QtCore.Qt.PenStyle.SolidLine}
        penColor = {
            True: self._dottedColor,
            False: self._color}
        penSize = {True: 1, False: 2}
        pen = QtGui.QPen(QtGui.QColor(penColor[mode]), penSize[mode])
        pen.setStyle(penType[mode])
        self.setPen(pen)

    def setInPort(self, port):
        self._inPort = port

    def setOutPort(self, port):
        self._outPort = port

    def getInPort(self):
        return self._inPort

    def getOutPort(self):
        return self._outPort

    def delete(self):
        if self._inPort:
            self._inPort._connectedPipes.remove(self)
        if self._outPort:
            self._outPort._connectedPipes.remove(self)
        scene = self.scene()
        if scene:
            scene.removeItem(self)


class PipeConnection(object):

    def __init__(self, startPort=None, endPort=None, scene=None):
        self._pipe = PipeItem()
        self._pipePortSetter = {
            'in':self._pipe.setInPort, 'out':self._pipe.setOutPort}
        self.fromPort = startPort
        self.toPort = endPort
        self._pos1 = None
        self._pos2 = None
        if self.fromPort:
            self._pos1 = self.fromPort.scenePos()
            self.fromPort.posCallbacks.append(self.setStartPos)
        if self.toPort:
            self._pos2 = self.toPort.scenePos()
        scene.addItem(self._pipe)

    def makePath(self, pos1, pos2):
        line = QtCore.QLineF(pos1, pos2)
        path = QtGui.QPainterPath()
        path.moveTo(line.x1(), line.y1())
        cp1_offset, cp2_offset = pos1.x(), pos2.x()
        parentRect = self.fromPort.parentItem().boundingRect()
        tangent = cp1_offset - cp2_offset
        if tangent < 0:
            tangent *= -1
        if tangent > parentRect.width():
            tangent = parentRect.width()
        if self.fromPort._portType == 'in':
            cp1_offset -= tangent
            cp2_offset += tangent
        elif self.fromPort._portType == 'out':
            cp1_offset += tangent
            cp2_offset -= tangent
        cp1 = QtCore.QPointF(cp1_offset, pos1.y())
        cp2 = QtCore.QPointF(cp2_offset, pos2.y())
        path.cubicTo(cp1, cp2, pos2)
        return path

    def setStartPos(self, pos):
        """
        set start point for the path

        Args:
            pos:

        """
        '''set start point for the path'''
        self._pos1 = pos
        path = self.makePath(self._pos1, self._pos2)
        self._pipe.setPath(path)

    def setEndPos(self, pos):
        """
        set end point for the path

        Args:
            pos:

        """
        self._pos2 = pos
        path = self.makePath(self._pos1, self._pos2)
        self._pipe.setPath(path)

    def setFromPort(self, fromPort):
        self.fromPort = fromPort
        if self.fromPort:
            self.pos1 = fromPort.scenePos()
            self.fromPort.posCallbacks.append(self.setStartPos)

    def setToPort(self, toPort):
        self.toPort = toPort
        if self.toPort:
            self.pos2 = self.toPort.scenePos()
            self.toPort.posCallbacks.append(self.setEndPos)
            self.toPort._connectedPipes.append(self._pipe)
            self._pipePortSetter[self.toPort._portType](self.fromPort)

            self.fromPort._connectedPipes.append(self._pipe)
            self._pipePortSetter[self.fromPort._portType](self.toPort)

    def deleteConnection(self):
        self._pipe.delete()
        if self.fromPort:
            self.fromPort.posCallbacks.remove(self.setStartPos)


class PortItem(QtGui.QGraphicsEllipseItem):
    """
    PortItem to a NodeItem
    """

    def __init__(self, parent=None, name='port', portType='out', limit=-1):
        super(PortItem, self).__init__(
            QtCore.QRectF(-4.0, -4.0, 8.0, 8.0), parent)
        self.setAcceptHoverEvents(True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self._connectedPipes = []
        self._colorDefault = ('#435967', '#1DCA97')
        self._colorClicked = ('#6A3C56', '#AF8BA6')
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[1]), 1))
        self._name = name
        self._portType = portType
        self._limit = limit
        self.posCallbacks = []

    def __str__(self):
        kwargs = {
            'name': self._name,
            'portType': self._portType,
            'limit': self._limit
        }
        return 'PortItem(\'{name}\', \'{portType}\', \'{limit}\')'.format(**kwargs)

    def itemChange(self, change, value):
        if change == self.ItemScenePositionHasChanged:
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super(PortItem, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[1])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[0]), 2))

    def hoverLeaveEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[1]), 1))

    def mousePressEvent(self, event):
        viewer = self.scene().getNodeViewer()
        viewer.startConnection(self)
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorClicked[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorClicked[1]), 2))
        # super(PortItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[1]), 2))
        # super(PortItem, self).mouseReleaseEvent(event)

    def getConnectedPipes(self):
        return self._connectedPipes

    def getConnectedPorts(self):
        ports = []
        for pipe in self._connectedPipes:
            if self._portType == 'in':
                ports.append(pipe.getOutPort())
            elif self._portType == 'out':
                ports.append(pipe.getInPort())
        return ports


class NodeSizerItem(QtGui.QGraphicsEllipseItem):
    """
    Node sizer handle class.
    """

    positionChanged = QtCore.Signal(str, str)

    def __init__(self, parent=None, size=6.0):
        super(NodeSizerItem, self).__init__(QtCore.QRectF(-size/2, -size/2, size, size), parent)
        self.posChangeCallbacks = []
        self.setPen(QtGui.QPen(QtGui.QColor('#A18961'), 1))
        self.setBrush(QtGui.QBrush(QtGui.QColor('#57431A')))
        self.setFlag(self.ItemIsSelectable, False)
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.SizeFDiagCursor))

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            x, y = value.x(), value.y()
            # TODO: make this a signal?
            # This cannot be a signal because this is not a QObject
            for cb in self.posChangeCallbacks:
                res = cb(x, y)
                if res:
                    x, y = res
                    value = QtCore.QPointF(x, y)
        return super(NodeSizerItem, self).itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self.parentItem().adjustSize()
        super(NodeSizerItem, self).mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        super(NodeSizerItem, self).mouseMoveEvent(event)
        self.setSelected(False)

    def mousePressEvent(self, event):
        super(NodeSizerItem, self).mousePressEvent(event)
        self.setSelected(False)

    def mouseReleaseEvent(self, event):
        super(NodeSizerItem, self).mouseReleaseEvent(event)
        self.setSelected(False)


class NodeItem(QtGui.QGraphicsRectItem):
    """
    Base Node Item
    """

    def __init__(self, name='Untitled_Node', parent=None):
        super(NodeItem, self).__init__(parent)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setPen(QtGui.QPen(QtGui.QColor('#186187'), 1))
        self._name = name
        self._colorBg = '#0B0E13'
        self._textColor = '#C4E8EB'
        self._width = 150
        self._height = 100

        # inputs and outputs of node:
        self._inputs = []
        self._inputsTexts = []
        self._outputs = []
        self._outputsTexts = []

        self._label = QtGui.QGraphicsTextItem(self._name, self)

        # Create corner for resize:
        self._sizer = NodeSizerItem(self)
        self._sizer.posChangeCallbacks.append(self.setSize)
        self._sizer.setFlag(self._sizer.ItemIsSelectable, True)
        self._sizer.setPos(self._width, self._height)
        self.setToolTip(
            'Resize: {}\n(Double Click to Reset)'.format(self._name))

        self.setBackgroundColor(self._colorBg)
        self.setTextColor(self._textColor)
        self.setResizable(True)

    def __str__(self):
        return 'NodeItem(name=\'{}\')'.format(self._name)

    def mouseMoveEvent(self, event):
        super(NodeItem, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        super(NodeItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super(NodeItem, self).mouseReleaseEvent(event)
        self.setBackgroundColor(self._colorBg)

    def paint(self, painter, option, widget):
        texts_items = [self._label]
        texts_items += self._outputsTexts
        texts_items += self._inputsTexts
        if not self.isSelected():
            for text in texts_items:
                text.setDefaultTextColor(QtGui.QColor(self._textColor))
            super(NodeItem, self).paint(painter, option, widget)
            return
        for text in texts_items:
            text.setDefaultTextColor(QtGui.QColor('#ffb72c'))
        rect = self.rect()
        x1, y1, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        painter.setBrush(QtGui.QColor('#674303'))
        painter.setPen(QtGui.QPen(QtGui.QColor('#ffb72c'), 1))
        painter.drawRect(x1, y1, w, h)

    def _calcSize(self):
        width = self._label.boundingRect().width() * 2
        if self._inputs:
            pWidths = [(p.boundingRect().width() * 2) for p in self._inputs]
            width += max(pWidths)
            width += pWidths[0]
        if self._outputs:
            pWidths = [(p.boundingRect().width() * 2) for p in self._outputs]
            width += max(pWidths)
            width += pWidths[0]
        pCount = max([len(self._inputs), len(self._outputs)]) + 1
        height = (PortItem().boundingRect().height() * 2) * pCount
        return width, height

    def _addPort(self, name, type, connectionLimit):
        port = PortItem(self, name, type, connectionLimit)
        text = QtGui.QGraphicsTextItem(port._name, self)
        text.setDefaultTextColor(QtGui.QColor('#5ED79F'))
        font = text.font()
        font.setPointSize(8)
        text.setFont(font)
        if type == 'in':
            self._inputs.append(port)
            self._inputsTexts.append(text)
        elif type == 'out':
            self._outputs.append(port)
            self._outputsTexts.append(text)
        self.adjustSize()

    def addInputPort(self, label='input', connectionLimit=-1):
        self._addPort(label, 'in', connectionLimit)

    def addOutputPort(self, label='output', connectionLimit=-1):
        self._addPort(label, 'out', connectionLimit)

    def adjustSize(self):
        self._width, self._height = self._calcSize()
        self._sizer.setPos(self._width, self._height)
        self.setSize(self._width, self._height)

    def setResizable(self, mode=True):
        self._sizer.setVisible(mode)

    def setSize(self, w, h):
        """
        Resize block function.

        Args:
            w (float): width of the circle.
            h (float): height of the circle.
        """
        # limit node size:
        if h < self._height:
            h = self._height
        if w < self._width:
            w = self._width

        self.setRect(0.0, 0.0, w, h)

        # center label:
        rect = self._label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        ly = lh * -1
        self._label.setPos(lx, ly)

        # update port positions:
        if len(self._inputs) == 1:
            paddingW = self._inputs[0].boundingRect().width()
            self._inputs[0].setPos(paddingW, h / 2)
        elif self._inputs:
            paddingW = self._inputs[0].boundingRect().width()
            paddingH = self._inputs[0].boundingRect().height()
            yChunk = h / (len(self._inputs) - 1)
            y = 0
            for port in self._inputs:
                if port == self._inputs[0]:
                    port.setPos(paddingW, paddingH)
                elif port == self._inputs[-1]:
                    port.setPos(paddingW, h - paddingH)
                else:
                    port.setPos(paddingW, y)
                y += yChunk

        if len(self._outputs) == 1:
            paddingW = self._outputs[0].boundingRect().width()
            self._outputs[0].setPos(paddingW, h / 2)
        elif self._outputs:
            paddingW = self._outputs[0].boundingRect().width()
            paddingH = self._outputs[0].boundingRect().height()
            yChunk = h / (len(self._outputs) - 1)
            y = 0
            for port in self._outputs:
                if port == self._outputs[0]:
                    port.setPos(w - paddingW, paddingH)
                elif port == self._outputs[-1]:
                    port.setPos(w - paddingW, h - paddingH)
                else:
                    port.setPos(w - paddingW, y)
                y += yChunk

        # update text position
        for idx, text in enumerate(self._inputsTexts):
            pRect = self._inputs[idx].boundingRect()
            pw, ph = pRect.width(), pRect.height()
            txtHeight = text.boundingRect().height()
            text.setPos(
                self._inputs[idx].x() + (pw / 2),
                self._inputs[idx].y() - (txtHeight / 2)
            )
        for idx, text in enumerate(self._outputsTexts):
            pRect = self._outputs[idx].boundingRect()
            pw, ph = pRect.width(), pRect.height()
            txtWidth = text.boundingRect().width()
            txtHeight = text.boundingRect().height()
            text.setPos(
                (self._outputs[idx].x() - txtWidth) - (pw / 2),
                self._outputs[idx].y() - (txtHeight / 2)
            )
        return w, h

    def setBackgroundColor(self, color):
        self._colorBg = color
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorBg)))

    def setTextColor(self, color):
        self._textColor = color
        self._label.setDefaultTextColor(QtGui.QColor(self._textColor))


class NodeScene(QtGui.QGraphicsScene):

    def __init__(self, parent=None, bgColor='#181818'):
        super(NodeScene, self).__init__(parent)
        self.setBackgroundColor(bgColor)

    def getNodeViewer(self):
        if self.views():
            return self.views()[0]
        return None

    def mouseMoveEvent(self, event):
        view = self.getNodeViewer()
        if view:
            view.sceneMouseMoveEvent(event)
        super(NodeScene, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        view = self.getNodeViewer()
        if view:
            view.sceneMouseReleaseEvent(event)
        super(NodeScene, self).mouseReleaseEvent(event)

    def setBackgroundColor(self, bgColor='#181818'):
        self._color = bgColor
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(self._color)))


class NodeViewer(QtGui.QGraphicsView):
    def __init__(self, scene, parent=None):
        super(NodeViewer, self).__init__(scene, parent)
        sceneArea = 3200.0
        self.setSceneRect(-(sceneArea/2), -(sceneArea/2), sceneArea, sceneArea)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self._startPort = None
        self._startedConnection = None
        self._extendConnection = False
        self._preExistingPipes = []

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            name = str(event.mimeData().data('component/name'))
            dropNode = NodeItem(name)
            dropNode.setPos(self.mapToScene(event.pos()))
            self.scene().addItem(dropNode)

    def startConnection(self, port):
        if port:
            self._startPort = port
            self._preExistingPipes = self._startPort.getConnectedPipes()
            self._startedConnection = PipeConnection(self._startPort, None, self.scene())

            # print self._startPort.name, len(self._preExistingPipes)
            # print self._startPort.getConnectedPorts()

            if len(self._preExistingPipes) == 1:
                if (port._portType == 'out') and (self._extendConnection):
                    return
                self._preExistingPipes[0].setDottedLine(True)

    def endConnection(self):
        self._startedConnection = None
        self._preExistingPipes = []

    def validateToPort(self, port):
        connectionChecks = [
            (port and port == self._startPort),
            (port and port._portType == self._startPort._portType),
            (port and port.parentItem() == self._startPort.parentItem()),
            (port == None)]
        if True in connectionChecks:
            return False
        return True

    def sceneMouseReleaseEvent(self, event):
        if self._startedConnection:
            # find destination port
            toPort = None
            for item in self.scene().items(event.scenePos()):
                if isinstance(item, PortItem):
                    toPort = item
                    break

            if (len(self._preExistingPipes) == 1) and (toPort == None):
                self._preExistingPipes[0].delete()

            if not self.validateToPort(toPort):
                if len(self._preExistingPipes) == 1:
                    self._preExistingPipes[0].setDottedLine(False)
                self._startedConnection.deleteConnection()
                self.endConnection()
                return

            if len(self._preExistingPipes) == 1:
                self._preExistingPipes[0].setDottedLine(False)

            if (toPort._limit != -1):
                while len(toPort.getConnectedPorts()) >= toPort._limit:
                    toPort.getConnectedPipes()[-1].delete()

            if self._startPort._portType == 'in':
                if len(self._preExistingPipes) == 1:
                    if toPort in self._startPort.getConnectedPorts():
                        self._startedConnection.deleteConnection()
                    else:
                        self._preExistingPipes[0].delete()
                        self._startedConnection.setToPort(toPort)
                        self._startedConnection.setEndPos(toPort.scenePos())
                    self.endConnection()
                    return
                else:
                    self._startedConnection.setToPort(toPort)
                    self._startedConnection.setEndPos(toPort.scenePos())


            elif self._startPort._portType == 'out':
                if len(self._preExistingPipes) == 1:
                    if toPort in self._startPort.getConnectedPorts():
                        self._startedConnection.deleteConnection()
                    else:
                        if not self._extendConnection:
                            self._preExistingPipes[0].delete()
                        self._startedConnection.setToPort(toPort)
                        self._startedConnection.setEndPos(toPort.scenePos())
                    self.endConnection()
                    return
                else:
                    self._startedConnection.setToPort(toPort)
                    self._startedConnection.setEndPos(toPort.scenePos())

            self.endConnection()

    def sceneMouseMoveEvent(self, event):
        if self._startedConnection:
            pos = event.scenePos()
            self._startedConnection.setEndPos(pos)

    def keyPressEvent(self, event):
        key = event.key()
        selection = self.scene().selectedItems()
        if key == QtCore.Qt.Key_Shift:
            self._extendConnection = True
        elif key == QtCore.Qt.Key_Alt:
            self.setDragMode(self.DragMode.ScrollHandDrag)
        elif key == QtCore.Qt.Key_F:
            if len(selection) == 1:
                self.centerOn(selection[0])
        elif (key == QtCore.Qt.Key_Delete) or (key == QtCore.Qt.Key_Backspace):
            for item in selection:
                self.scene().removeItem(item)
        super(NodeViewer, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self._extendConnection = False
        self.setDragMode(self.DragMode.NoDrag)
        super(NodeViewer, self).keyReleaseEvent(event)
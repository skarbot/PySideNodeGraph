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
        if self.fromPort.portType == 'in':
            cp1_offset -= tangent
            cp2_offset += tangent
        elif self.fromPort.portType == 'out':
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

    def setFromPort(self):
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
            self._pipePortSetter[self.toPort.portType](self.fromPort)

            self.fromPort._connectedPipes.append(self._pipe)
            self._pipePortSetter[self.fromPort.portType](self.toPort)

    def deleteConnection(self):
        self._pipe.delete()
        if self.fromPort:
            self.fromPort.posCallbacks.remove(self.setStartPos)


class PortItem(QtGui.QGraphicsEllipseItem):
    """
    PortItem to a NodeItem
    """

    def __init__(self, parent=None, name='port', portType='out', connectionLimit=-1, portSize=8.0):
        super(PortItem, self).__init__(QtCore.QRectF(-portSize/2, -portSize/2, portSize, portSize), parent)
        self.setAcceptHoverEvents(True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self._connectedPipes = []
        self._colorDefault = ('#435967', '#5E8E9C')
        self._colorClicked = ('#6A3C56', '#AF8BA6')
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[1]), 2))
        self.name = name
        self.portType = portType
        self.connectionLimit = connectionLimit
        self.posCallbacks = []

    def __str__(self):
        return 'PortItem(\'{}\', \'{}\')'.format(self.name, self.portType)

    def itemChange(self, change, value):
        if change == self.ItemScenePositionHasChanged:
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super(PortItem, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[1])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[0]), 1))

    def hoverLeaveEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorDefault[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._colorDefault[1]), 2))

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
            if self.portType == 'in':
                ports.append(pipe.getOutPort())
            elif self.portType == 'out':
                ports.append(pipe.getInPort())
        return ports


class NodeSizerItem(QtGui.QGraphicsEllipseItem):
    """
    Node handle that can be moved by the mouse
    """

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
            return value
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
        self.setPen(QtGui.QPen(QtGui.QColor('#3C3C3C'), 1))
        self.name = name
        self._width = 50.0
        self._height = 100.0
        self._colorBg = '#0B0E13'
        self._colorSelected = '#8e612e'
        self._textColor = '#B3B3B3'
        self._label = QtGui.QGraphicsTextItem(self.name, self)

        # inputs and outputs of node:
        self._inputs = []
        self._inputsTexts = []
        self._outputs = []
        self._outputsTexts = []

        # Create corner for resize:
        self._sizer = NodeSizerItem(self)
        self._sizer.posChangeCallbacks.append(self.setSize)
        self._sizer.setFlag(self._sizer.ItemIsSelectable, True)
        self._sizer.setPos(self._width, self._height)
        self.setToolTip(
            'Resize: {}\n(Double Click to Reset)'.format(self.name))

        self.setBackgroundColor(self._colorBg)
        self.setTextColor(self._textColor)
        self.setResizable(True)

    def __str__(self):
        return 'NodeItem(name=\'{}\')'.format(self.name)

    def mouseMoveEvent(self, event):
        super(NodeItem, self).mouseMoveEvent(event)
    #     self.setSelected(False)
    #
    def mousePressEvent(self, event):
        super(NodeItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super(NodeItem, self).mouseReleaseEvent(event)
        self.setBackgroundColor(self._colorBg)
    #     self.setSelected(False)

    def paint(self, painter, option, widget):
        if not self.isSelected():
            super(NodeItem, self).paint(painter, option, widget)
            return
        rect = self.rect()
        x1, y1, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        painter.setBrush(QtGui.QColor('#8e612e'))
        painter.setPen(QtGui.QColor('#ffb72c'))
        painter.drawRect(x1, y1, w, h)

    def _calcSize(self):
        inWidth, outWidth = 0, 0
        portHeight = 50
        if self._inputs:
            for text in self._inputsTexts:
                if text.boundingRect().width() > inWidth:
                    inWidth = text.boundingRect().width()
            inWidth += (self._inputs[0].boundingRect().width() * 2)
            portHeight = self._inputs[0].boundingRect().height()
        if self._outputs:
            for text in self._outputsTexts:
                if text.boundingRect().width() > outWidth:
                    outWidth = text.boundingRect().width()
            outWidth += (self._outputs[0].boundingRect().width() * 2)
            portHeight = self._outputs[0].boundingRect().height()

        width = (inWidth + outWidth) + (self._label.boundingRect().width()/2)
        height = portHeight * (max(len(self._inputs), len(self._outputs)) + 4)
        return width, height

    def _addPort(self, name, type, connectionLimit):
        port = PortItem(self, name, type, connectionLimit)
        text = QtGui.QGraphicsTextItem(port.name, self)
        text.setDefaultTextColor(QtGui.QColor(self._textColor))
        font = text.font()
        font.setPointSize(10)
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
        labelRect = self._label.boundingRect()
        inPortRect = None
        outPortRect = None
        if self._inputsTexts:
            portRect = self._inputsTexts[0].boundingRect()
        if self._outputsTexts:
            outPortRect = self._outputsTexts[0].boundingRect()

        # Limit the block size:
        if h < self._height:
            h = self._height
        if w < self._width:
            w = self._width
        self.setRect(0.0, 0.0, w, h)
        # center label:
        rect = self._label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        ly = (h - lh) / 2
        self._label.setPos(lx, ly)
        # update port positions:
        padding = (0, 50)
        if len(self._inputs) == 1:
            self._inputs[0].setPos(padding[0], h / 2)
        elif len(self._inputs) > 1:
            y = 5
            dy = (h - 10) / (len(self._inputs) - 1)
            for inp in self._inputs:
                if inp == self._inputs[0]:
                    inp.setPos(padding[0], y + padding[1])
                elif inp == self._inputs[-1]:
                    inp.setPos(padding[0], y - padding[1])
                else:
                    inp.setPos(padding[0], y)
                y += dy
        if len(self._outputs) == 1:
            self._outputs[0].setPos(w-padding[0], h / 2)
        elif len(self._outputs) > 1:
            y = 5
            dy = (h - 10) / (len(self._outputs) - 1)
            for outp in self._outputs:
                if outp == self._outputs[0]:
                    outp.setPos(w-padding[0], y + padding[1])
                elif outp == self._outputs[-1]:
                    outp.setPos(w-padding[0], y - padding[1])
                else:
                    outp.setPos(w-padding[0], y)
                y += dy
        # update text position
        for idx, txt in enumerate(self._inputsTexts):
            pRect = self._inputs[idx].boundingRect()
            pw, ph = pRect.width(), pRect.height()
            tHeight = txt.boundingRect().height()
            txt.setPos(self._inputs[idx].x()+(pw/2), self._inputs[idx].y()-(tHeight/2))
        for idx, txt in enumerate(self._outputsTexts):
            pRect = self._outputs[idx].boundingRect()
            pw, ph = pRect.width(), pRect.height()
            tWidth = txt.boundingRect().width()
            tHeight = txt.boundingRect().height()
            txt.setPos((self._outputs[idx].x()-tWidth)-(pw/2), self._outputs[idx].y()-(tHeight/2))
        return w, h

    def setBackgroundColor(self, color):
        self._colorBg = color
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorBg)))

    def setSelectedColor(self, color):
        self._colorSelected = color
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._colorSelected)))

    def setTextColor(self, color):
        self._textColor = color
        self._label.setDefaultTextColor(QtGui.QColor(self._textColor))
        portTexts = self._inputsTexts + self._outputsTexts
        for text in portTexts:
            text.setDefaultTextColor(QtGui.QColor(self._textColor))


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
                if (port.portType == 'out') and (self._extendConnection):
                    return
                self._preExistingPipes[0].setDottedLine(True)

    def endConnection(self):
        self._startedConnection = None
        self._preExistingPipes = []

    def validateToPort(self, port):
        connectionChecks = [
            (port and port == self._startPort),
            (port and port.portType == self._startPort.portType),
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

            if (toPort.connectionLimit != -1):
                while len(toPort.getConnectedPorts()) >= toPort.connectionLimit:
                    toPort.getConnectedPipes()[-1].delete()

            if self._startPort.portType == 'in':
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


            elif self._startPort.portType == 'out':
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
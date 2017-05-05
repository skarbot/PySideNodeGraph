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
        viewer = self.scene().get_node_viewer()
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
        self.parentItem().reset_size()
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


class BaseRectItem(QtGui.QGraphicsRectItem):
    """
    Base Shape Item
    """

    def __init__(self, parent):
        super(BaseRectItem, self).__init__(parent)
        self._antialiasing = False
        self._color_bg = '#2F3234'
        self._color_border = '#575B5D'
        self.set_node_color()

    def paint(self, painter, option, widget):
        painter.setRenderHint(painter.Antialiasing, self._antialiasing)
        super(BaseRectItem, self).paint(painter, option, widget)

    def set_node_color(self, color='#2F3234', border='#575B5D'):
        self._color_bg = color
        self._color_border = border
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_bg)))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_border), 1))


class NodeTextBackground(BaseRectItem):

    def __init__(self, parent):
        super(NodeTextBackground, self).__init__(parent)

    def mousePressEvent(self, event):
        parent = self.parentItem()
        if parent:
            parent.setSelected(True)


class NodeItem(BaseRectItem):
    """
    Base Node Item
    """

    def __init__(self, name='Node', parent=None):
        super(NodeItem, self).__init__(parent)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # node
        self._text_bg_item = NodeTextBackground(self)
        self._text_item = QtGui.QGraphicsTextItem(name, self._text_bg_item)
        self._color_text = '#6b7781'
        self._width = 150
        self._height = 100

        # ports in/out
        self._inputs = []
        self._inputsTexts = []
        self._outputs = []
        self._outputsTexts = []

        # node sizer
        self._sizer = NodeSizerItem(self)
        self._sizer.posChangeCallbacks.append(self.set_node_size)
        self._sizer.setFlag(self._sizer.ItemIsSelectable, True)
        self._sizer.setPos(self._width, self._height)
        self.setToolTip(
            'Resize: {}\n(Double Click to Reset)'.format(self.node_name()))

        # initialize setup
        self.set_text_color()
        self.set_resizable(True)

    def __str__(self):
        return 'NodeItem(name=\'{}\')'.format(self.node_name())

    def paint(self, painter, option, widget):
        if self.isSelected():
            self._text_bg_item.set_node_color('#070b10', '#070b10')
            rect = self.rect()
            painter.setRenderHint(painter.Antialiasing, self._antialiasing)
            painter.setBrush(QtGui.QColor('#674303'))
            painter.setPen(QtGui.QPen(QtGui.QColor('#ffb72c'), 1))
            painter.drawRect(rect.x(), rect.y(), rect.width(), rect.height())
            text_color = QtGui.QColor('#ffb72c')
            self._text_item.setDefaultTextColor(QtGui.QColor('#1d2e43'))
        else:
            super(NodeItem, self).paint(painter, option, widget)
            self._text_bg_item.set_node_color('#040b0e', '#0a0d0e')
            text_color = QtGui.QColor(self._color_text)
            self._text_item.setDefaultTextColor(text_color)

        texts_items = self._inputsTexts + self._outputsTexts
        for text in texts_items:
            text.setDefaultTextColor(text_color)

    # def mouseMoveEvent(self, event):
    #     super(NodeItem, self).mouseMoveEvent(event)

    # def mousePressEvent(self, event):
    #     super(NodeItem, self).mousePressEvent(event)

    # def mouseReleaseEvent(self, event):
    #     super(NodeItem, self).mouseReleaseEvent(event)

    def _calc_size(self):
        width = self._text_item.boundingRect().width() * 2
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

    def _add_port(self, name, type, limit):
        port = PortItem(self, name, type, limit)
        text = QtGui.QGraphicsTextItem(port._name, self)
        text.setDefaultTextColor(QtGui.QColor(self._color_text))
        font = text.font()
        font.setPointSize(8)
        text.setFont(font)
        if type == 'in':
            self._inputs.append(port)
            self._inputsTexts.append(text)
        elif type == 'out':
            self._outputs.append(port)
            self._outputsTexts.append(text)
        self.reset_size()

    def node_name(self):
        """
        Get the name of the node.
        Returns:
            str: node name.
        """
        return self._text_item.toPlainText()

    def set_node_name(self, name='node'):
        """
        Set the node name.
        Args:
            name (str): name of the node.
        """
        self._text_item.setPlainText(name)

    def set_text_color(self, color='#C4E8EB'):
        """
        Set the color of the node text.
        Args:
            color (str): color in HEX format.
        """
        self._color_text = color
        self._text_item.setDefaultTextColor(QtGui.QColor(self._color_text))

    def set_resizable(self, mode=True):
        """
        Allow the node to be resizeable.
        Args:
            mode (bool): true if the node can be resized.
        """
        self._sizer.setVisible(mode)

    def reset_size(self):
        """
        Reset the node size to its initial width & height.
        """
        self._width, self._height = self._calc_size()
        self._sizer.setPos(self._width, self._height)
        self.set_node_size(self._width, self._height)

    def add_input_port(self, label='port', limit=-1):
        """
        Adds an input port to the node.
        Args:
            label (str): name to display next to the port
            limit (int): the amount of connections a port can have.
        """
        self._add_port(label, 'in', limit)

    def add_output_port(self, label='port', limit=-1):
        """
        Adds an output port to the node.
        Args:
            label (str): name to display next to the port
            limit (int): the amount of connections a port can have.
        """
        self._add_port(label, 'out', limit)

    def set_node_size(self, width, height):
        """
        Sets the node size with the given width x height.
        Args:
            width (float): width of the node.
            height (float): height of the node.
        """
        # limit size:
        height = self._height if height < self._height else height
        width = self._width if width < self._width else width
        self.setRect(0.0, 0.0, width, height)

        # update label and background position:
        t_rect = self._text_item.boundingRect()
        tw, th = t_rect.width(), t_rect.height()
        ty = (th + 2) * -1
        self._text_bg_item.setRect(0, 0, width, th)
        self._text_bg_item.setPos(0, ty)
        self._text_item.setPos(2, 0)

        # update port positions:
        if len(self._inputs) == 1:
            padding_w = self._inputs[0].boundingRect().width()
            self._inputs[0].setPos(padding_w, height / 2)
        elif self._inputs:
            padding_w = self._inputs[0].boundingRect().width()
            padding_h = self._inputs[0].boundingRect().height()
            y_chunk = height / (len(self._inputs) - 1)
            y = 0
            for port in self._inputs:
                if port == self._inputs[0]:
                    port.setPos(padding_w, padding_h)
                elif port == self._inputs[-1]:
                    port.setPos(padding_w, height - padding_h)
                else:
                    port.setPos(padding_w, y)
                y += y_chunk

        if len(self._outputs) == 1:
            padding_w = self._outputs[0].boundingRect().width()
            self._outputs[0].setPos(padding_w, height / 2)
        elif self._outputs:
            padding_w = self._outputs[0].boundingRect().width()
            padding_h = self._outputs[0].boundingRect().height()
            y_chunk = height / (len(self._outputs) - 1)
            y = 0
            for port in self._outputs:
                if port == self._outputs[0]:
                    port.setPos(width - padding_w, padding_h)
                elif port == self._outputs[-1]:
                    port.setPos(width - padding_w, height - padding_h)
                else:
                    port.setPos(width - padding_w, y)
                y += y_chunk

        # update text position
        for idx, text in enumerate(self._inputsTexts):
            p_rect = self._inputs[idx].boundingRect()
            pw, ph = p_rect.width(), p_rect.height()
            txt_height = text.boundingRect().height()
            text.setPos(
                self._inputs[idx].x() + (pw / 2),
                self._inputs[idx].y() - (txt_height / 2)
            )
        for idx, text in enumerate(self._outputsTexts):
            p_rect = self._outputs[idx].boundingRect()
            pw, ph = p_rect.width(), p_rect.height()
            txt_width = text.boundingRect().width()
            txt_height = text.boundingRect().height()
            text.setPos(
                (self._outputs[idx].x() - txt_width) - (pw / 2),
                self._outputs[idx].y() - (txt_height / 2)
            )
        return width, height


class NodeScene(QtGui.QGraphicsScene):

    def __init__(self, parent=None, bg_color='#181818'):
        super(NodeScene, self).__init__(parent)
        self.set_background_color(bg_color)

    def mouseMoveEvent(self, event):
        view = self.get_node_viewer()
        if view:
            view.sceneMouseMoveEvent(event)
        super(NodeScene, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        view = self.get_node_viewer()
        if view:
            view.sceneMouseReleaseEvent(event)
        super(NodeScene, self).mouseReleaseEvent(event)

    def get_node_viewer(self):
        if self.views():
            return self.views()[0]
        return None

    def set_background_color(self, bg_color='#181818'):
        self._color_bg = bg_color
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(self._color_bg)))


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
#!/usr/bin/python
from PySide import QtGui, QtCore


class Pipe(QtGui.QGraphicsPathItem):
    """
    Base pipe item.
    """

    def __init__(self, color='#C28D34', dotted_color='#6b3c6a'):
        super(Pipe, self).__init__(None)
        self.setFlag(self.ItemIsSelectable, False)
        self._dotted = False
        self._color = color
        self._color_dotted = dotted_color
        self._in_port = None
        self._out_port = None
        self.set_dotted(False)

    def __str__(self):
        class_name = self.__class__.__name__
        return '{}()'.format(class_name)

    def set_pipe_color(self, color):
        """
        Sets the color of the pipe.
        Args:
            color (str): color of the pipe in HEX format. 
        """
        self._color = color
        self.set_dotted(False)

    def set_dotted(self, mode=False):
        """
        Sets the style of the pipe to dotted mode.
        Args:
            mode (bool): true if 
        """
        self._dotted = mode
        if self._dotted:
            pen = QtGui.QPen(QtGui.QColor(self._color_dotted), 1)
            pen.setStyle(QtCore.Qt.PenStyle.DashDotDotLine)
        else:
            pen = QtGui.QPen(QtGui.QColor(self._color), 2)
            pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        self.setPen(pen)

    def set_in_port(self, port):
        """
        Set input for the pipe.        
        Args:
            port (Port): the connected input port.
        """
        self._in_port = port

    def set_out_port(self, port):
        """
        Set output for the pipe.        
        Args:
            port (Port): the connected output port.
        """
        self._out_port = port

    def get_in_port(self):
        """
        Get the connected input port.
        Returns:
            Port: the connected port.
        """
        return self._in_port

    def get_out_port(self):
        """
        Get the connected output port.
        Returns:
            Port: the connected port.
        """
        return self._out_port

    def dotted(self):
        """
        Mode of the pipe if it is dotted.
        Returns:
            bool: true if dotted.
        """
        return self._dotted

    def delete(self):
        """
        Remove the pipe from the current scene and 
        detach from the connected ports.
        """
        if self._in_port:
            self._in_port._pipe = None
        if self._out_port:
            self._out_port._pipe = None
        if self.scene():
            self.scene().removeItem(self)


class PipeConnectionGenerator(object):
    """
    Pipe connection object that will create the connection pipe 
    to the targeted node ports.
    """

    def __init__(self, from_port=None, to_port=None, scene=None):
        self._pipe = Pipe()
        self._from_port = from_port
        self._to_port = to_port
        self._pos1 = None
        self._pos2 = None
        if self._from_port:
            self._pos1 = self._from_port.scenePos()
            self._from_port.pos_callbacks.append(self.set_start_pos)
        if self._to_port:
            self._pos2 = self._to_port.scenePos()
        scene.addItem(self._pipe)

    def __str__(self):
        return '{}(from_port={}, to_port={})'.format(
            self.__class__.__name__, str(self._from_port), str(self._to_port)
        )

    def _make_path(self, pos1, pos2):
        line = QtCore.QLineF(pos1, pos2)
        path = QtGui.QPainterPath()
        path.moveTo(line.x1(), line.y1())
        cp1_offset, cp2_offset = pos1.x(), pos2.x()
        rect = self._from_port.parentItem().boundingRect()
        tangent = cp1_offset - cp2_offset
        if tangent < 0:
            tangent *= -1
        if tangent > rect.width():
            tangent = rect.width()
        if self._from_port.type() == 'in':
            cp1_offset -= tangent
            cp2_offset += tangent
        elif self._from_port.type() == 'out':
            cp1_offset += tangent
            cp2_offset -= tangent
        cp1 = QtCore.QPointF(cp1_offset, pos1.y())
        cp2 = QtCore.QPointF(cp2_offset, pos2.y())
        path.cubicTo(cp1, cp2, pos2)
        return path

    def set_start_pos(self, pos):
        """
        Set start point for the path.
        Args:
            pos (QtCore.QPointF): start position for the pipe.  
        """
        self._pos1 = pos
        path = self._make_path(self._pos1, self._pos2)
        self._pipe.setPath(path)

    def set_end_pos(self, pos):
        """
        Set end point for the path.
        Args:
            pos (QtCore.QPointF): end position for the pipe.
        """
        self._pos2 = pos
        path = self._make_path(self._pos1, self._pos2)
        self._pipe.setPath(path)

    def set_from_port(self, port):
        self._from_port = port
        if self._from_port:
            self._pos1 = port.scenePos()
            self._from_port.pos_callbacks.append(self.set_start_pos)

    def set_to_port(self, port):
        self._to_port = port
        if self._to_port:
            self._pos2 = self._to_port.scenePos()
            self._to_port.pos_callbacks.append(self.set_end_pos)
            self._to_port._connected_pipe = self._pipe
            self._from_port._connected_pipe = self._pipe
            port_setter = {
                'out': self._pipe.set_in_port,
                'in': self._pipe.set_out_port
            }
            port_setter[self._to_port.type()](self._from_port)
            port_setter[self._from_port.type()](self._to_port)
            # assign pipe to the ports
            self._from_port._pipe = self._pipe
            self._to_port._pipe = self._pipe

    def delete_connection(self):
        self._pipe.delete()
        if self._from_port:
            self._from_port.pos_callbacks.remove(self.set_start_pos)


class Port(QtGui.QGraphicsEllipseItem):
    """
    Base Port object.
    """

    def __init__(self, parent=None, name='port', port_type='out'):
        rect = QtCore.QRectF(-4.0, -4.0, 8.0, 8.0)
        super(Port, self).__init__(rect, parent)
        self.setAcceptHoverEvents(True)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self._pipe = None
        self._color_default = ('#435967', '#1DCA97')
        self._color_clicked = ('#6A3C56', '#AF8BA6')
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_default[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_default[1]), 1))
        self._name = name
        self._port_type = port_type
        self.pos_callbacks = []

    def __str__(self):
        class_name = self.__class__.__name__
        return '{}(\'{}\', \'{}\')'.format(
            class_name, self._name, self._port_type
        )

    def itemChange(self, change, value):
        if change == self.ItemScenePositionHasChanged:
            for cb in self.pos_callbacks:
                cb(value)
            return value
        return super(Port, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_default[1])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_default[0]), 2))

    def hoverLeaveEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_default[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_default[1]), 1))

    def mousePressEvent(self, event):
        viewer = self.scene().get_node_viewer()
        viewer.start_connection(self)
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_clicked[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_clicked[1]), 2))
        # super(PortItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_default[0])))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_default[1]), 2))
        # super(PortItem, self).mouseReleaseEvent(event)

    def node(self):
        """
        Get the node of the current port.
        Returns:
            BaseNode: node that's connected to the port.
        """
        return self.parentItem()

    def name(self):
        """
        Get the name of the current port.
        Returns:
            str: port name.
        """
        return self._name

    def type(self):
        """
        Query the port type whether it's a in or out. 
        Returns:
            str: in or out.
        """
        return self._port_type

    def connected_pipe(self):
        """
        Gets the connected pipe object.
        Returns:
            Pipe: the object of the connected pipe.
        """
        return self._pipe

    def connected_port(self):
        """
        Gets the connected port object.
        Returns:
            Port: the object of the connected port.
        """
        if self._pipe:
            if self._port_type is 'in':
                return self._pipe.get_out_port()
            elif self._port_type is 'out':
                return self._pipe.get_in_port()
        return None


class BaseRectFrame(QtGui.QGraphicsRectItem):
    """
    Base frame for a node object.
    """

    def __init__(self, parent):
        super(BaseRectFrame, self).__init__(parent)
        self._antialiasing = False
        self._color_bg = '#2F3234'
        self._color_border = '#3c4042'
        self.set_node_color()

    def paint(self, painter, option, widget):
        painter.setRenderHint(painter.Antialiasing, self._antialiasing)
        super(BaseRectFrame, self).paint(painter, option, widget)

    def set_node_color(self, color='#2F3234', border='#3c4042'):
        """
        Set the background & border color of the node.
        Args:
            color (str): background color in HEX format.
            border (str): border color in HEX format.
        """
        self._color_bg = color
        self._color_border = border
        self.setBrush(QtGui.QBrush(QtGui.QColor(self._color_bg)))
        self.setPen(QtGui.QPen(QtGui.QColor(self._color_border), 1))


class NodeLabelBackground(BaseRectFrame):
    """
    Base node label background shape.
    """

    def __init__(self, parent):
        super(NodeLabelBackground, self).__init__(parent)

    def mousePressEvent(self, event):
        parent = self.parentItem()
        if parent:
            parent.setSelected(True)


class BaseNode(BaseRectFrame):
    """
    Base node object.
    """

    def __init__(self, name='Node', icon=None, parent=None):
        super(BaseNode, self).__init__(parent)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # node
        self._text_bg_item = NodeLabelBackground(self)
        self._text_item = QtGui.QGraphicsTextItem(name, self._text_bg_item)
        self._color_text = '#6b7781'
        self._color_text_bg = '#292c2f'
        self._width = 150
        self._height = 100
        # ports in/out
        self._inputs = []
        self._inputsTexts = []
        self._outputs = []
        self._outputsTexts = []
        # initialize
        self.set_text_color()

    def __str__(self):
        class_name = self.__class__.__name__
        return '{}(\'{}\')'.format(class_name, self.name())

    def paint(self, painter, option, widget):
        if self.isSelected():
            self._text_bg_item.set_node_color('#070b10', '#070b10')
            rect = self.rect()
            painter.setRenderHint(painter.Antialiasing, self._antialiasing)
            painter.setBrush(QtGui.QColor('#674303'))
            painter.setPen(QtGui.QPen(QtGui.QColor('#774e03'), 1))
            painter.drawRect(rect.x(), rect.y(), rect.width(), rect.height())
            text_color = QtGui.QColor('#ffb72c')
            self._text_item.setDefaultTextColor(QtGui.QColor('#C58828'))
        else:
            super(BaseNode, self).paint(painter, option, widget)
            self._text_bg_item.set_node_color(
                self._color_text_bg, self._color_text_bg)
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
        height = (Port().boundingRect().height() * 2) * pCount
        return width, height

    def _add_port(self, name, type):
        port = Port(self, name, type)
        text = QtGui.QGraphicsTextItem(port.name(), self)
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

    def add_input_port(self, label='port'):
        """
        Adds an input port to the node.
        Args:
            label (str): name to display next to the port
        """
        self._add_port(label, 'in')

    def add_output_port(self, label='port'):
        """
        Adds an output port to the node.
        Args:
            label (str): name to display next to the port
        """
        self._add_port(label, 'out')

    def name(self):
        """
        Get the name of the node.
        Returns:
            str: node name.
        """
        return self._text_item.toPlainText()

    def set_name(self, name='node'):
        """
        Set the node name.
        Args:
            name (str): name of the node.
        """
        self._text_item.setPlainText(name)

    def set_icon(self, icon):
        """
        Sets the icon for the current node.
        Args:
            icon (str): path to the icon image.
        """
        raise NotImplementedError

    def set_text_color(self, color='#C4E8EB'):
        """
        Set the color of the node text.
        Args:
            color (str): color in HEX format.
        """
        self._color_text = color
        self._text_item.setDefaultTextColor(QtGui.QColor(self._color_text))

    def set_size(self, width, height):
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
        ty = (th + 1) * -1
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

    def reset_size(self):
        """
        Reset the node size to its initial width & height.
        """
        self._width, self._height = self._calc_size()
        self.set_size(self._width, self._height)

    def delete(self):
        """
        Remove node from the node graph.
        """
        ports = self._inputs + self._outputs
        for port in ports:
            if port.connected_pipe():
                port.connected_pipe().delete()
        if self.scene():
            self.scene().removeItem(self)


class NodeScene(QtGui.QGraphicsScene):

    def __init__(self, parent=None, bg_color='#212121'):
        super(NodeScene, self).__init__(parent)
        self.set_background_color(bg_color)

    def __str__(self):
        class_name = self.__class__.__name__
        return '{}()'.format(class_name)

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

    def set_background_color(self, bg_color='#212121'):
        self._color_bg = bg_color
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(self._color_bg)))


class NodeViewer(QtGui.QGraphicsView):
    def __init__(self, scene, parent=None):
        super(NodeViewer, self).__init__(scene, parent)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        scene_area = 3200.0
        self.setSceneRect(
            -(scene_area / 2), -(scene_area / 2), scene_area, scene_area
        )
        self._start_port = None
        self._connection_started = None

    def __str__(self):
        class_name = self.__class__.__name__
        return '{}()'.format(class_name)

    # def dragEnterEvent(self, event):
    #     if event.mimeData().hasFormat('component/name'):
    #         event.accept()
    #
    # def dragMoveEvent(self, event):
    #     if event.mimeData().hasFormat('component/name'):
    #         event.accept()
    #
    # def dropEvent(self, event):
    #     if event.mimeData().hasFormat('component/name'):
    #         name = str(event.mimeData().data('component/name'))
    #         dropNode = NodeItem(name)
    #         dropNode.setPos(self.mapToScene(event.pos()))
    #         self.scene().addItem(dropNode)

    def start_connection(self, port):
        # start connection when the port is clicked.
        if not port:
            return
        self._start_port = port
        if self._start_port.connected_pipe():
            # switch start point if pipe exists.
            self._start_port = self._start_port.connected_port()

        self._connection_started = PipeConnectionGenerator(
            self._start_port, None, self.scene()
        )

    def end_connection(self):
        self._connection_started = None

    def sceneMouseReleaseEvent(self, event):
        if self._connection_started:
            # find destination port
            to_port = None
            for item in self.scene().items(event.scenePos()):
                if isinstance(item, Port):
                    to_port = item
                    break
            # validate port and connection
            end_connection = False
            connected_pipe = self._start_port.connected_pipe()
            if not to_port:
                if connected_pipe:
                    connected_pipe.delete()
                end_connection = True
            elif to_port is self._start_port:
                if connected_pipe:
                    connected_pipe.set_dotted(False)
                end_connection = True
            elif to_port.type() is self._start_port.type():
                if connected_pipe:
                    connected_pipe.set_dotted(False)
                end_connection = True
            elif to_port.node() is self._start_port.node():
                if connected_pipe:
                    connected_pipe.set_dotted(False)
                end_connection = True

            # do not remove connected pipe if to_port == from_port
            if to_port and to_port.connected_pipe():
                if to_port is not self._start_port:
                    to_port.connected_pipe().delete()

            if end_connection:
                self._connection_started.delete_connection()
                self.end_connection()
                return

            # make the connection.
            if connected_pipe:
                connected_pipe.delete()
            self._connection_started.set_to_port(to_port)
            self._connection_started.set_end_pos(to_port.scenePos())
            self.end_connection()

    def sceneMouseMoveEvent(self, event):
        if self._connection_started:
            self._connection_started.set_end_pos(event.scenePos())
            connected_pipe = self._start_port.connected_pipe()
            if connected_pipe and not connected_pipe.dotted():
                connected_pipe.set_dotted(True)

    def keyPressEvent(self, event):
        key = event.key()
        selection = self.scene().selectedItems()
        if key == QtCore.Qt.Key_Alt:
            self.setDragMode(self.DragMode.ScrollHandDrag)
        elif key == QtCore.Qt.Key_F:
            if len(selection) is 1:
                self.centerOn(selection[0])
        elif key == QtCore.Qt.Key_Delete or key == QtCore.Qt.Key_Backspace:
            for item in selection:
                if isinstance(item, BaseNode):
                    item.delete()
        super(NodeViewer, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.setDragMode(self.DragMode.NoDrag)
        super(NodeViewer, self).keyReleaseEvent(event)
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

    def delete(self):
        """
        Remove port from the node.
        """
        if self._pipe:
            self._pipe.delete()
        if self.scene():
            self.scene().removeItem(self)






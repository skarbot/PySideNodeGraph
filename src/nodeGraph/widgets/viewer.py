from PySide import QtGui, QtCore

from .pipe import PipeConnectionGenerator, Port


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
        # elif key == QtCore.Qt.Key_Delete or key == QtCore.Qt.Key_Backspace:
        #     for item in selection:
        #         if isinstance(item, BaseNode):
        #             item.delete()
        super(NodeViewer, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.setDragMode(self.DragMode.NoDrag)
        super(NodeViewer, self).keyReleaseEvent(event)
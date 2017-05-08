from PySide import QtGui, QtCore

from .pipe import Port


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
        self._inputs_texts = []
        self._outputs = []
        self._outputs_texts = []
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

        texts_items = self._inputs_texts + self._outputs_texts
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
            self._inputs_texts.append(text)
        elif type == 'out':
            self._outputs.append(port)
            self._outputs_texts.append(text)
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
        for idx, text in enumerate(self._inputs_texts):
            p_rect = self._inputs[idx].boundingRect()
            pw, ph = p_rect.width(), p_rect.height()
            txt_height = text.boundingRect().height()
            text.setPos(
                self._inputs[idx].x() + (pw / 2),
                self._inputs[idx].y() - (txt_height / 2)
            )
        for idx, text in enumerate(self._outputs_texts):
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
        if self.scene():
            self.scene().removeItem(self)
        port_texts = self._inputs_texts + self._outputs_texts
        for text in port_texts:
            if self.scene():
                self.scene().removeItem(text)
        ports = self._inputs + self._outputs
        for port in ports:
            port.delete()

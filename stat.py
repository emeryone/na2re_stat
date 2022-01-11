import sqlite3
import sys

from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *
import pyqtgraph as pg

import json
from datetime import datetime

dialog = None
graph = None
help = None
con = sqlite3.connect("payments.db")
cur = con.cursor()


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


def format_date(dt):
    if dt == 0:
        return "-"
    datetime_obj = datetime.fromtimestamp(dt)
    return datetime_obj.strftime("%d.%m.%y %H:%M:%S")


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        global dialog, graph, help, con, cur
        self.buttonStat = None
        self.buttonHelp = None
        self.tableWidget = None
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.resize(800, 600)
        self.setup_ui(self.centralWidget)
        self.setWindowTitle("Информация о платежах")
        self.tableWidget.clicked.connect(self.on_click)
        self.tableWidget.doubleClicked.connect(self.on_double_click)
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.on_header_click)
        self.buttonStat.clicked.connect(self.show_stat)
        self.buttonHelp.clicked.connect(self.show_help)
        self.order_cols = ["id", "user, request_time", "request_time", "finish_time", "result, request_time",
                           "download_count, user", "download_time, user"]
        self.order_by = 1
        self.saved_row = -1
        self.show_table()

    def setup_ui(self, widget):
        widget.setObjectName("Widget")
        widget.setLayout(QGridLayout())
        layout = widget.layout()
        font = QtGui.QFont()
        font.setFamily("Verdana")
        widget.setFont(font)
        self.tableWidget = QtWidgets.QTableWidget()
        layout.addWidget(self.tableWidget, 1, 0, 2, 5)
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.tableWidget.setFont(font)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(6, item)
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setHighlightSections(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setHighlightSections(False)
        self.buttonStat = QtWidgets.QPushButton()
        self.buttonStat.setGeometry(QtCore.QRect(30, 10, 113, 32))
        self.buttonStat.setObjectName("pushButton")
        layout.addWidget(self.buttonStat, 0, 0)
        self.buttonHelp = QtWidgets.QPushButton()
        self.buttonHelp.setGeometry(QtCore.QRect(160, 10, 113, 32))
        self.buttonHelp.setObjectName("pushButton_2")
        layout.addWidget(self.buttonHelp, 0, 1)

        self.retranslate_ui(widget)
        QtCore.QMetaObject.connectSlotsByName(widget)

    def retranslate_ui(self, widget):
        _translate = QtCore.QCoreApplication.translate
        widget.setWindowTitle(_translate("Widget", "Widget"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Widget", "ИД"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Widget", "Клиент"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Widget", "Создано"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Widget", "Оплачено"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Widget", "Транзакция"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("Widget", "Загрузки"))
        item = self.tableWidget.horizontalHeaderItem(6)
        item.setText(_translate("Widget", "Последняя"))
        self.buttonStat.setText(_translate("Widget", "Статистика"))
        self.buttonHelp.setText(_translate("Widget", "Справка"))

    def closeEvent(self, event):
        dialog.close()
        help.close()
        graph.close()
        event.accept()

    def show_stat(self):
        graph.show()

    def show_help(self):
        help.show()

    def prn_dict(self, my_dict):
        for k, v in my_dict.items():
            if isinstance(v, dict):
                print(k + ":")
                self.prn_dict(v)
                continue
            print(k + " : " + str(v))

    def show_details(self, r):
        result = cur.execute(
            "SELECT payments.request_raw, payments.responce_raw, payments.finish_raw, payments.request_time, \
            payments.responce_time, payments.finish_time, items.file \
            FROM payments, items where payments.book_id = items.id and payments.id = " + r).fetchone()
        #clear_layout(dialog.widget.layout())
        dialog.reset()
        dialog.show()
        dialog.add_text(result[6])
        if len(result[0]) > 0:
            j = json.loads(result[0])
            dialog.show_dict(j, "=> " + format_date(result[3]))
        if len(result[2]) > 0:
            j = json.loads(result[1])
            dialog.show_dict(j, "<= " + format_date(result[4]))
        if len(result[2]) > 0:
            j = json.loads(result[2])
            dialog.show_dict(j, "<= " + format_date(result[5]))

    def add_cell(self, i, j, v, date_flag=False):
        if date_flag:
            v = format_date(int(v))
        item = QTableWidgetItem(str(v))
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.tableWidget.setItem(i, j, item)

    def select_row(self, r):
        self.saved_row = r
        for i in range(self.tableWidget.columnCount()):
            self.tableWidget.item(r, i).setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            self.tableWidget.item(r, i).setSelected(True)

    def deselect_row(self):
        if self.saved_row > -1:
            for i in range(self.tableWidget.columnCount()):
                self.tableWidget.item(self.saved_row, i).setSelected(False)
                self.tableWidget.item(self.saved_row, i).setFlags(QtCore.Qt.ItemIsEnabled)
        self.saved_row = -1

    def get_id(self, r):
        return self.tableWidget.item(r, 0).text()

    # Событие: дабл-клик по строке табицы
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_double_click(self, index):
        self.deselect_row()
        self.select_row(index.row())
        self.show_details(self.get_id(index.row()))

    # Событие: клик по строке
    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_click(self, index):
        print(index.row())
        self.deselect_row()
        dialog.close()

    # Событие: клик по заголовку столбца
    @QtCore.pyqtSlot(int)
    def on_header_click(self, index):
        print(index)
        self.order_by = index
        self.show_table()

    def show_table(self):
        result = cur.execute(
            "SELECT id, user, request_time, finish_time, result, download_count, download_time FROM payments ORDER BY "
            + self.order_cols[self.order_by]).fetchall()
        self.tableWidget.setRowCount(len(result))
        self.tableWidget.setColumnCount(len(result[0]))
        for i, elem in enumerate(result):
            self.add_cell(i, 0, elem[0])
            self.add_cell(i, 1, elem[1])
            self.add_cell(i, 2, elem[2], True)
            self.add_cell(i, 3, elem[3], True)
            self.add_cell(i, 4, elem[4])
            self.add_cell(i, 5, elem[5])
            self.add_cell(i, 6, elem[6], True)
        self.tableWidget.resizeColumnsToContents()


class Graph(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Транзакции")
        self.setGeometry(100, 100, 800, 500)
        layout = QGridLayout()
        self.setLayout(layout)
        self.plot = None
        self.year = None
        self.month = None
        self.with_faults = None
        self.ui_components()

    def date_changed(self, index):
        self.draw_plot()

    def draw_plot(self):
        year = int(self.year.currentText())
        month = self.month.currentIndex()
        result = cur.execute(
            "SELECT request_time, finish_time, download_time, download_count, result \
            FROM payments ORDER BY request_time").fetchall()
        x = []
        y1 = []
        if month == 0:
            for i in range(1, 13):
                x.append(i)
            y1 = [0] * 12
            for i, row in enumerate(result):
                dt = datetime.fromtimestamp(row[0])
                y = int(dt.strftime("%Y"))
                m = int(dt.strftime("%m")) - 1
                if y == year:
                    if row[4] == "succeeded" or self.with_faults.isChecked():
                        y1[m] = y1[m] + 1
        else:
            for i in range(1, 32):
                x.append(i)
            y1 = [0] * 31
            for i, row in enumerate(result):
                dt = datetime.fromtimestamp(row[0])
                y = int(dt.strftime("%Y"))
                m = int(dt.strftime("%m"))
                d = int(dt.strftime("%d")) - 1
                if y == year and m == month:
                    if row[4] == "succeeded" or self.with_faults.isChecked():
                        y1[d] = y1[d] + 1
        plot = pg.plot()
        bargraph = pg.BarGraphItem(x=x, height=y1, width=0.6, brush='g')
        plot.addItem(bargraph)
        if self.plot is not None:
            # Дективация экземпляра pg.plot() вызывает ошибку. Вероятно в деструкторе не отключаются
            # обработчики событий. На практике на работу не влияет.
            # qt.qpa.window: <QNSWindow: 0x13dd57ea0;
            # contentView=<QNSView: 0x13dd57bd0;
            # QCocoaWindow(0x600003b1c370,
            # window=QWidgetWindow(0x6000028544e0, name="PlotWidgetClassWindow"))>>
            # has active key-value observers (KVO)! These will stop working now that the window is recreated,
            # and will result in exceptions when the observers are removed.
            # Break in QCocoaWindow::recreateWindowIfNeeded to debug.
            self.layout().replaceWidget(self.plot, plot)
            self.plot.deleteLater()
            self.plot = None
        else:
            self.layout().addWidget(plot, 0, 1, 5, 1)
        self.plot = plot

    # method for components
    def ui_components(self):
        global dialog, graph, con, cur
        layout = self.layout()
        self.year = QComboBox()
        dt = datetime.now()
        year1 = 2021
        year2 = int(dt.strftime("%Y")) + 1
        for i in reversed(range(year1, year2)):
            self.year.addItem(str(i))
        self.month = QComboBox()
        self.month.addItem("Весь год")
        self.month.addItem("Январь")
        self.month.addItem("Февраль")
        self.month.addItem("Март")
        self.month.addItem("Апрель")
        self.month.addItem("Май")
        self.month.addItem("Июнь")
        self.month.addItem("Июль")
        self.month.addItem("Август")
        self.month.addItem("Сентябрь")
        self.month.addItem("Октябрь")
        self.month.addItem("Ноябрь")
        self.month.addItem("Декабрь")
        self.with_faults = QCheckBox("Включая неуспешные")
        layout.addWidget(self.year, 0, 0)
        layout.addWidget(self.month, 1, 0)
        layout.addWidget(self.with_faults, 2, 0)
        self.draw_plot()
        self.year.currentIndexChanged.connect(self.date_changed)
        self.month.currentIndexChanged.connect(self.date_changed)
        # Обработчик события выводин на передний план главное окно. Похоже на баг в Qt.
        self.with_faults.stateChanged.connect(self.date_changed)


class Details(QDialog):
    def __init__(self):
        super().__init__()
        self.level = 0
        self.line = 0
        self.setWindowTitle("Взаимодействие с платежной системой")
        self.setGeometry(100, 100, 800, 500)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.widget = QWidget()
        self.widget.setGeometry(100, 100, 800, 500)
        self.widget.setLayout(QGridLayout())
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)
        self.layout().addWidget(self.scroll)

    def show_dict(self, d, t=""):
        if not len(d) > 0:
            return
        self.level = 0
        if len(t) > 0:
            label = QtWidgets.QLabel()
            label.setText(t)
            self.widget.layout().addWidget(label, self.line, self.level)
            frame = QFrame()
            frame.setFrameShape(QFrame.HLine)
            self.widget.layout().addWidget(frame, self.line + 1, 0, 1, 4)
            self.line = self.line + 2
        self.prn_dict(d)
        self.line = self.line + 1

    def prn_dict(self, my_dict):
        layout = self.widget.layout()
        for k, v in my_dict.items():
            if isinstance(v, dict):
                label = QtWidgets.QLabel("attribute" + str(self.level))
                label.setText(k)
                layout.addWidget(label, self.line, self.level)
                self.level = self.level + 1
                self.line = self.line + 1
                self.prn_dict(v)
                self.level = self.level - 1
                continue
            label = QtWidgets.QLabel("attribute" + str(self.level))
            label.setText(k)
            layout.addWidget(label, self.line, self.level)
            label = QtWidgets.QLabel("attribute" + str(self.level))
            label.setText(str(v))
            layout.addWidget(label, self.line, self.level + 1)
            self.line = self.line + 1

    def show_json(self, j):
         self.prn_dict(j)

    def add_text(self, t=""):
        if len(t) > 0:
            label = QtWidgets.QLabel()
            label.setText(str(t))
            self.widget.layout().addWidget(label, self.line, self.level)
            frame = QFrame()
            frame.setFrameShape(QFrame.HLine)
            self.widget.layout().addWidget(frame, self.line + 1, 0, 1, 4)
            self.line = self.line + 2

    def reset(self):
        self.level = 0
        self.line = 0
        clear_layout(self.widget.layout())


class Help(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Справка")
        self.setGeometry(100, 100, 600, 300)
        self.setLayout(QGridLayout())
        self.add_help("Одинарный щелчек мышью по заголовку столбца - сортировка")
        self.add_help("Двойной щелчек мышью по строке таблицы - информация по обмену данными с плптежным шлюзом")
        self.add_help("Статистика - диаграмма количества платежей по месяцам")
        self.add_help("Столбцы:")
        self.add_help("Создано - Дата переход покупателя в платежный шлюз")
        self.add_help("Оплачено - Дата проведение платежа (Если '-' - платеж не произведен)")
        self.add_help("Загрузки - Оставшееся число загрузок")
        self.add_help("Последняя - Дата последней загрузки")

    def add_help(self, s):
        label = QtWidgets.QLabel()
        label.setText(s)
        self.layout().addWidget(label)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = Details()
    graph = Graph()
    help = Help()
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec())
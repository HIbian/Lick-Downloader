import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.window import *
from grab import Grab


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.lineEdit_2.setText('127.0.0.1')
        self.lineEdit_3.setText('7890')

        self.grab_thread = Grab('', '')
        self.grab_thread.process_signal.connect(self.update_processbar)
        self.grab_thread.started.connect(self.started_thread)
        self.grab_thread.finished.connect(self.finished_thread)

        self.pushButton.clicked.connect(self.grab_picture)

        self.outputfile = None
        self.grab_thread.update_text_signal.connect(self.text_browser_update)

    def text_browser_update(self, outline):
        self.textBrowser.append(outline)

    def update_processbar(self, count, total):
        self.progressBar.setMaximum(total)
        self.progressBar.setValue(count)

    def started_thread(self):
        # deactivate_items
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.lineEdit_3.setEnabled(False)
        self.pushButton.setEnabled(False)

    def finished_thread(self):
        # activate_items
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.lineEdit_3.setEnabled(True)
        self.pushButton.setEnabled(True)

    def grab_picture(self):
        self.grab_thread.keyword = self.lineEdit.text()
        proxy_addr = self.lineEdit_2.text()
        port = self.lineEdit_3.text()
        if proxy_addr == '' or port == '':
            self.grab_thread.proxy = None
        else:
            self.grab_thread.proxies = {
                'http://': 'http://{}:{}'.format(proxy_addr, port),
                'https://': 'http://{}:{}'.format(proxy_addr, port),
            }
        self.grab_thread.header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
        }
        self.grab_thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

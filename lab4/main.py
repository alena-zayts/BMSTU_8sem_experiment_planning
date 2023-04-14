import sys
from PyQt5.QtWidgets import QApplication
from mainwindow import mywindow

if __name__ == "__main__":
    app = QApplication([])
    application = mywindow()
    application.show()

    sys.exit(app.exec())

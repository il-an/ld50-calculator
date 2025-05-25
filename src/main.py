import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from biocalculator.util import karber


class LD50Calculator(QMainWindow):
    """
    main window for the LD50 calculator application
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LD50 Калькулятор")
        self.setMinimumSize(600, 400)

        # Главный виджет и компоновка
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Параметры эксперимента
        self.params_layout = QGridLayout()

        # Количество животных в группе
        self.params_layout.addWidget(QLabel("Количество животных в группе:"), 0, 0)
        self.max_animals_edit = QLineEdit("8")
        self.max_animals_edit.setValidator(QIntValidator(1, 1000))
        self.params_layout.addWidget(self.max_animals_edit, 0, 1)

        # Коэффициент дозы
        self.params_layout.addWidget(QLabel("Коэффициент дозы:"), 0, 2)
        self.dose_coef_edit = QLineEdit("10")
        self.dose_coef_edit.setValidator(QDoubleValidator(0.1, 100, 2))
        self.dose_coef_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.dose_coef_edit, 0, 3)

        # Количество доз
        self.params_layout.addWidget(QLabel("Количество доз:"), 1, 0)
        self.num_doses_edit = QLineEdit("8")
        self.num_doses_edit.setValidator(QIntValidator(2, 100))
        self.num_doses_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.num_doses_edit, 1, 1)

        self.main_layout.addLayout(self.params_layout)

        # Таблица для ввода данных
        self.table = QTableWidget(8, 2)
        self.table.setHorizontalHeaderLabels(["Доза", "Количество умерших"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self.validate_table_item)
        self.main_layout.addWidget(self.table)

        # Автоматическое заполнение доз
        self.updating_table = False
        self.update_table()

        # Кнопка для расчета и поле для результата
        self.bottom_layout = QHBoxLayout()

        self.calculate_button = QPushButton("Рассчитать LD50")
        self.calculate_button.clicked.connect(self.calculate_ld50)
        self.bottom_layout.addWidget(self.calculate_button)

        self.result_label = QLabel("Результат: ")
        self.bottom_layout.addWidget(self.result_label)

        self.main_layout.addLayout(self.bottom_layout)

    def validate_table_item(self, item):
        if self.updating_table:
            return
        # Проверяем только ячейки столбца "Количество умерших"
        if item.column() == 1:
            # Если ячейка пустая, заменяем на 0
            if item.text().strip() == "":
                item.setText("0")
            # Проверка, что введено число
            try:
                value = int(item.text())
                # Проверка, что не превышает максимальное количество животных
                max_animals = int(self.max_animals_edit.text())
                if value > max_animals:
                    item.setText(str(max_animals))
            except ValueError:
                item.setText("0")
        # Проверяем только первую дозу на корректность (число > 0)
        if item.column() == 0 and item.row() == 0:
            try:
                value = float(item.text())
                if value <= 0:
                    value = 1.0
                # Форматируем до двух знаков после запятой
                item.setText(f"{value:.2f}")
            except ValueError:
                item.setText("1.00")
            # После изменения первой дозы обновляем остальные
            self.update_doses_from_first()

    def update_doses_from_first(self):
        try:
            self.updating_table = True
            num_doses = int(self.num_doses_edit.text())
            coef = float(self.dose_coef_edit.text())
            first_dose_item = self.table.item(0, 0)
            if first_dose_item is None:
                return
            try:
                start_dose = float(first_dose_item.text())
            except Exception:
                start_dose = 1000000.0
                first_dose_item.setText(str(start_dose))
            # Обновляем остальные дозы
            for i in range(1, num_doses):
                dose = start_dose / (coef ** i)
                dose_item = QTableWidgetItem(f"{dose:.2f}")
                dose_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(i, 0, dose_item)
            self.updating_table = False
        except Exception:
            self.updating_table = False

    def update_table(self):
        try:
            self.updating_table = True
            # Сохраняем значения умерших перед обновлением
            died_values = {}
            for i in range(self.table.rowCount()):
                died_item = self.table.item(i, 1)
                if died_item is not None:
                    died_values[i] = died_item.text()

            num_doses = int(self.num_doses_edit.text())
            coef = float(self.dose_coef_edit.text())

            self.table.blockSignals(True)
            self.table.setRowCount(num_doses)

            # Первая доза — редактируемая
            first_dose = 1000000.0
            first_dose_item = self.table.item(0, 0)
            if first_dose_item is not None:
                try:
                    first_dose = float(first_dose_item.text())
                except Exception:
                    pass
            dose_item = QTableWidgetItem(f"{first_dose:.2f}")
            dose_item.setFlags(dose_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(0, 0, dose_item)

            # Остальные дозы — не редактируемые
            for i in range(1, num_doses):
                dose = first_dose / (coef ** i)
                dose_item = QTableWidgetItem(f"{dose:.2f}")
                dose_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(i, 0, dose_item)

            # Восстанавливаем значения умерших или ставим 0
            for i in range(num_doses):
                if i in died_values:
                    self.table.setItem(i, 1, QTableWidgetItem(died_values[i]))
                else:
                    self.table.setItem(i, 1, QTableWidgetItem("0"))

            self.table.blockSignals(False)
            self.updating_table = False
        except (ValueError, ZeroDivisionError):
            self.updating_table = False

    def calculate_ld50(self):
        try:
            max_animals = int(self.max_animals_edit.text())
            num_doses = int(self.num_doses_edit.text())

            doses = []
            died = []
            for i in range(num_doses):
                dose_val = float(self.table.item(i, 0).text())
                doses.append(dose_val)
                died.append(int(self.table.item(i, 1).text()))

            result = karber(
                doses=doses,
                max_animals=max_animals,
                died=died,
            )

            self.result_label.setText(f"Результат: LD50 = {result:.2f}")

        except Exception as e:
            self.result_label.setText(f"Ошибка: {e!s}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LD50Calculator()
    window.show()
    sys.exit(app.exec())

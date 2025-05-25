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

        # Максимальная доза
        self.params_layout.addWidget(QLabel("Максимальная доза:"), 0, 0)
        self.max_dose_edit = QLineEdit("1000000")
        self.max_dose_edit.setValidator(QIntValidator(1, 999999999))
        self.max_dose_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.max_dose_edit, 0, 1)

        # Количество животных в группе
        self.params_layout.addWidget(QLabel("Количество животных в группе:"), 0, 2)
        self.max_animals_edit = QLineEdit("8")
        self.max_animals_edit.setValidator(QIntValidator(1, 1000))
        self.params_layout.addWidget(self.max_animals_edit, 0, 3)

        # Коэффициент дозы
        self.params_layout.addWidget(QLabel("Коэффициент дозы:"), 1, 0)
        self.dose_coef_edit = QLineEdit("10")
        self.dose_coef_edit.setValidator(QDoubleValidator(0.1, 100, 2))
        self.dose_coef_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.dose_coef_edit, 1, 1)

        # Количество доз
        self.params_layout.addWidget(QLabel("Количество доз:"), 1, 2)
        self.num_doses_edit = QLineEdit("8")
        self.num_doses_edit.setValidator(QIntValidator(2, 100))
        self.num_doses_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.num_doses_edit, 1, 3)

        self.main_layout.addLayout(self.params_layout)

        # Таблица для ввода данных
        self.table = QTableWidget(8, 2)
        self.table.setHorizontalHeaderLabels(["Доза", "Количество умерших"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self.validate_table_item)
        self.main_layout.addWidget(self.table)

        # Автоматическое заполнение доз
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

    def update_table(self):
        try:
            # Сохраняем текущие значения умерших перед обновлением
            died_values = {}
            for i in range(self.table.rowCount()):
                item = self.table.item(i, 1)
                if item is not None:
                    died_values[i] = item.text()

            num_doses = int(self.num_doses_edit.text())
            max_dose = int(self.max_dose_edit.text())
            coef = float(self.dose_coef_edit.text())

            # Отключаем сигналы таблицы перед изменениями
            self.table.blockSignals(True)

            # Устанавливаем новое количество строк
            self.table.setRowCount(num_doses)

            # Заполняем дозы
            for i in range(num_doses):
                dose = max_dose / (coef ** i)

                # Доза
                dose_item = QTableWidgetItem(f"{dose:.2f}")
                dose_item.setFlags(dose_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Неизменяемая ячейка
                self.table.setItem(i, 0, dose_item)

                # Восстанавливаем значения умерших или ставим 0
                if i in died_values:
                    self.table.setItem(i, 1, QTableWidgetItem(died_values[i]))
                else:
                    self.table.setItem(i, 1, QTableWidgetItem("0"))

            # Включаем сигналы обратно
            self.table.blockSignals(False)

        except (ValueError, ZeroDivisionError):
            pass

    def calculate_ld50(self):
        try:
            # Собираем данные
            max_dose = int(self.max_dose_edit.text())
            max_animals = int(self.max_animals_edit.text())
            dose_coef = float(self.dose_coef_edit.text())
            num_doses = int(self.num_doses_edit.text())

            died = []
            for i in range(num_doses):
                died.append(int(self.table.item(i, 1).text()))

            # Вычисляем LD50
            result = karber(
                max_dose=max_dose,
                max_animals=max_animals,
                died=died,
                dose_coefficient=dose_coef,
                number_of_doses=num_doses,
            )

            self.result_label.setText(f"Результат: LD50 = {result:.2f}")

        except Exception as e:
            self.result_label.setText(f"Ошибка: {e!s}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LD50Calculator()
    window.show()
    sys.exit(app.exec())

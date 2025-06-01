import sys

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,  # добавлено
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


class SurvivalPlot(QWidget):
    def __init__(
        self, doses, died, max_animals, ld50=None, parent=None, mode="LD50",
    ):
        super().__init__(parent)
        self.setWindowTitle("График выживаемости")
        self.setMinimumSize(800, 600)
        self.setWindowFlag(Qt.WindowType.Window, True)

        layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.plot_survival(doses, died, max_animals, ld50, mode)

    def plot_survival(self, doses, died, max_animals, ld50=None, mode="LD50"):
        self.figure.clear()

        ax = self.figure.add_subplot(111)

        if mode == "LD50":
            survival_percent = [(1 - d / max_animals) * 100 for d in died]
            label = "Выживаемость, %"
            title = "График выживаемости"
            line_label = "LD50"
        elif mode == "ED50":
            # ED50: считаем по выжившим
            survival_percent = [(d / max_animals) * 100 for d in died]
            label = "Эффективность, %"
            title = "График эффективности"
            line_label = "ED50"

        ax.plot(doses, survival_percent, "o-", linewidth=2, markersize=8)

        ax.set_xscale("log")

        if ld50 is not None:
            ax.axvline(x=ld50, color="r", linestyle="--", alpha=0.7)
            ax.text(
                ld50 * 1.1,
                50,
                f"{line_label} = {ld50:.2f}",
                color="r",
                fontsize=12,
            )

            ax.axhline(y=50, color="r", linestyle="--", alpha=0.3)

        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Доза (логарифмическая шкала)", fontsize=12)
        ax.set_ylabel(label, fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_ylim(-5, 105)

        self.canvas.draw()


class LD50Calculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LD50 Калькулятор")
        self.setMinimumSize(600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.params_layout = QGridLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["LD50", "ED50"])
        self.mode_combo.currentIndexChanged.connect(self.update_labels)
        self.params_layout.addWidget(QLabel("Режим расчёта:"), 0, 0)
        self.params_layout.addWidget(self.mode_combo, 0, 1)

        self.params_layout.addWidget(
            QLabel("Количество животных в группе:"), 1, 0,
        )
        self.max_animals_edit = QLineEdit("8")
        self.max_animals_edit.setValidator(QIntValidator(1, 1000))
        self.params_layout.addWidget(self.max_animals_edit, 1, 1)

        self.params_layout.addWidget(QLabel("Коэффициент дозы:"), 1, 2)
        self.dose_coef_edit = QLineEdit("10")
        self.dose_coef_edit.setValidator(QDoubleValidator(0.1, 100, 2))
        self.dose_coef_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.dose_coef_edit, 1, 3)

        self.params_layout.addWidget(QLabel("Количество доз:"), 2, 0)
        self.num_doses_edit = QLineEdit("8")
        self.num_doses_edit.setValidator(QIntValidator(2, 100))
        self.num_doses_edit.editingFinished.connect(self.update_table)
        self.params_layout.addWidget(self.num_doses_edit, 2, 1)

        self.main_layout.addLayout(self.params_layout)

        self.table = QTableWidget(8, 2)
        self.table.setHorizontalHeaderLabels(["Доза", "Количество умерших"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch,
        )
        self.table.itemChanged.connect(self.validate_table_item)
        self.main_layout.addWidget(self.table)

        self.updating_table = False
        self.update_table()

        self.bottom_layout = QHBoxLayout()

        self.calculate_button = QPushButton("Рассчитать LD50")
        self.calculate_button.clicked.connect(self.calculate_ld50)
        self.bottom_layout.addWidget(self.calculate_button)

        self.plot_button = QPushButton("Построить график")
        self.plot_button.clicked.connect(self.show_survival_plot)
        self.bottom_layout.addWidget(self.plot_button)

        self.result_label = QLabel("Результат: ")
        self.bottom_layout.addWidget(self.result_label)

        self.main_layout.addLayout(self.bottom_layout)

        self.last_ld50 = None
        self.survival_plot = None

    def update_labels(self):
        mode = self.mode_combo.currentText()
        if mode == "LD50":
            self.table.setHorizontalHeaderLabels(
                ["Доза", "Количество умерших"],
            )
            self.calculate_button.setText("Рассчитать LD50")
        else:
            self.table.setHorizontalHeaderLabels(
                ["Доза", "Количество выживших"],
            )
            self.calculate_button.setText("Рассчитать ED50")
        self.result_label.setText("Результат: ")
        self.last_ld50 = None

    def validate_table_item(self, item):
        if self.updating_table:
            return
        if item.column() == 1:
            if item.text().strip() == "":
                item.setText("0")
            try:
                value = int(item.text())
                max_animals = int(self.max_animals_edit.text())
                if value > max_animals:
                    item.setText(str(max_animals))
            except ValueError:
                item.setText("0")
        if item.column() == 0 and item.row() == 0:
            try:
                value = float(item.text())
                if value <= 0:
                    value = 1.0
                item.setText(f"{value:.2f}")
            except ValueError:
                item.setText("1.00")
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
            for i in range(1, num_doses):
                dose = start_dose / (coef**i)
                dose_item = QTableWidgetItem(f"{dose:.2f}")
                dose_item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled,
                )
                self.table.setItem(i, 0, dose_item)
            self.updating_table = False
        except Exception:
            self.updating_table = False

    def update_table(self):
        try:
            self.updating_table = True
            died_values = {}
            for i in range(self.table.rowCount()):
                died_item = self.table.item(i, 1)
                if died_item is not None:
                    died_values[i] = died_item.text()

            num_doses = int(self.num_doses_edit.text())
            coef = float(self.dose_coef_edit.text())

            self.table.blockSignals(True)
            self.table.setRowCount(num_doses)

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

            for i in range(1, num_doses):
                dose = first_dose / (coef**i)
                dose_item = QTableWidgetItem(f"{dose:.2f}")
                dose_item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled,
                )
                self.table.setItem(i, 0, dose_item)

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
            coef = int(self.dose_coef_edit.text())

            doses = []
            died = []
            for i in range(num_doses):
                dose_val = float(self.table.item(i, 0).text())
                doses.append(dose_val)
                val = int(self.table.item(i, 1).text())
                died.append(val)

            max_dose = doses[0]

            mode = self.mode_combo.currentText()
            if mode == "LD50":
                result = karber(
                    max_dose=max_dose,
                    max_animals=max_animals,
                    died=died,
                    dose_coefficient=coef,
                    number_of_doses=num_doses,
                )
                self.last_ld50 = result
                self.result_label.setText(f"Результат: LD50 = {result:.2f}")
            elif mode == "ED50":
                result = karber(
                    max_dose=max_dose,
                    max_animals=max_animals,
                    died=died,
                    dose_coefficient=coef,
                    number_of_doses=num_doses,
                )
                self.last_ld50 = result
                self.result_label.setText(f"Результат: ED50 = {result:.2f}")

        except Exception as e:
            self.result_label.setText(f"Ошибка: {e!s}")
            self.last_ld50 = None

    def show_survival_plot(self):
        try:
            max_animals = int(self.max_animals_edit.text())
            num_doses = int(self.num_doses_edit.text())

            doses = []
            died = []
            for i in range(num_doses):
                dose_val = float(self.table.item(i, 0).text())
                doses.append(dose_val)
                died.append(int(self.table.item(i, 1).text()))

            ld50 = self.last_ld50
            mode = self.mode_combo.currentText()
            if ld50 is None:
                try:
                    max_dose = doses[0]
                    coef = int(self.dose_coef_edit.text())
                    if mode == "LD50":
                        ld50 = karber(
                            max_dose=max_dose,
                            max_animals=max_animals,
                            died=died,
                            dose_coefficient=coef,
                            number_of_doses=num_doses,
                        )
                    else:
                        ld50 = karber(
                            max_dose=max_dose,
                            max_animals=max_animals,
                            died=died,
                            dose_coefficient=coef,
                            number_of_doses=num_doses,
                        )
                except Exception:
                    ld50 = None

            if self.survival_plot is not None:
                self.survival_plot.raise_()
                self.survival_plot.activateWindow()
                return

            self.survival_plot = SurvivalPlot(
                doses, died, max_animals, ld50, self, mode,
            )
            self.survival_plot.show()

            parent = self

            class SurvivalPlotWithClose(SurvivalPlot):
                def closeEvent(self, event):
                    parent.survival_plot = None
                    event.accept()

            self.survival_plot.closeEvent = (
                SurvivalPlotWithClose.closeEvent.__get__(
                    self.survival_plot, SurvivalPlot,
                )
            )

        except Exception as e:
            self.result_label.setText(f"Ошибка построения графика: {e!s}")

    def closeEvent(self, event):
        if self.survival_plot is not None:
            self.survival_plot.close()
            self.survival_plot = None
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LD50Calculator()
    window.show()
    sys.exit(app.exec())

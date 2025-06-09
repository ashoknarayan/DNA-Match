import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton,
    QVBoxLayout, QLabel, QLineEdit, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class NeedlemanWunschVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Needleman-Wunsch Visualizer")
        self.font = QFont("Courier New", 12)
        self.zoom_factor = 1.0
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Input section
        self.seq1_input = QLineEdit("GATTAGC")
        self.seq2_input = QLineEdit("GTACGTG")
        self.match_input = QLineEdit("1")
        self.mismatch_input = QLineEdit("-1")
        self.gap_input = QLineEdit("-2")
        self.solve_button = QPushButton("Solve")
        self.solve_button.clicked.connect(self.solve)

        for inp in [self.seq1_input, self.seq2_input, self.match_input, self.mismatch_input, self.gap_input]:
            inp.setFont(self.font)
            inp.setMaximumWidth(100)

        input_layout = QGridLayout()
        input_layout.addWidget(self.seq1_input, 0, 0)
        input_layout.addWidget(self.seq2_input, 0, 1)
        input_layout.addWidget(self.match_input, 0, 2)
        input_layout.addWidget(self.mismatch_input, 0, 3)
        input_layout.addWidget(self.gap_input, 0, 4)
        input_layout.addWidget(self.solve_button, 0, 5)
        layout.addLayout(input_layout)

        # Scrollable area for DP matrix
        self.scroll_area = QScrollArea()
        self.matrix_widget = QWidget()
        self.grid = QGridLayout(self.matrix_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.matrix_widget)
        layout.addWidget(self.scroll_area)

        # Output
        self.output_label = QLabel("")
        self.output_label.setFont(self.font)
        layout.addWidget(self.output_label)

        self.setLayout(layout)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            angle = event.angleDelta().y()
            self.zoom_factor += 0.1 if angle > 0 else -0.1
            self.zoom_factor = max(0.5, min(self.zoom_factor, 3.0))
            self.update_matrix_font()

    def update_matrix_font(self):
        new_font = QFont("Courier New", int(12 * self.zoom_factor))
        for i in range(self.grid.count()):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setFont(new_font)
        self.output_label.setFont(new_font)

    def solve(self):
        seq1 = "-" + self.seq1_input.text().upper()
        seq2 = "-" + self.seq2_input.text().upper()
        m, n = len(seq1), len(seq2)

        try:
            match = int(self.match_input.text())
            mismatch = int(self.mismatch_input.text())
            gap = int(self.gap_input.text())
        except:
            self.output_label.setText("Invalid scoring parameters.")
            return

        dp = [[0] * n for _ in range(m)]
        trace = [[None] * n for _ in range(m)]

        for i in range(1, m):
            dp[i][0] = i * gap
            trace[i][0] = '↑'
        for j in range(1, n):
            dp[0][j] = j * gap
            trace[0][j] = '←'

        for i in range(1, m):
            for j in range(1, n):
                score = match if seq1[i] == seq2[j] else mismatch
                diag = dp[i-1][j-1] + score
                up = dp[i-1][j] + gap
                left = dp[i][j-1] + gap
                dp[i][j] = max(diag, up, left)
                trace[i][j] = '↖' if dp[i][j] == diag else ('↑' if dp[i][j] == up else '←')

        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        # Store data
        self.dp = dp
        self.trace = trace
        self.seq1 = seq1
        self.seq2 = seq2
        self.labels = [[None for _ in range(n)] for _ in range(m)]

        # Headers
        for j in range(n):
            lbl = QLabel(seq2[j])
            lbl.setFont(self.font)
            lbl.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(lbl, 0, j + 1)
        for i in range(m):
            lbl = QLabel(seq1[i])
            lbl.setFont(self.font)
            lbl.setAlignment(Qt.AlignCenter)
            self.grid.addWidget(lbl, i + 1, 0)

        # Start animated DP filling
        self.fill_i = 0
        self.fill_j = 0
        self.fill_timer = QTimer()
        self.fill_timer.timeout.connect(self.fill_step)
        self.fill_timer.start(1)

    def fill_step(self):
        if self.fill_i >= len(self.seq1):
            self.fill_timer.stop()
            self.traceback()
            return
        if self.fill_j >= len(self.seq2):
            self.fill_j = 0
            self.fill_i += 1
            return
        i, j = self.fill_i, self.fill_j
        label = QLabel(f"{self.dp[i][j]}\n{self.trace[i][j] or ''}")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(self.font)
        label.setStyleSheet("border: 1px solid gray;")
        self.grid.addWidget(label, i + 1, j + 1)
        self.labels[i][j] = label
        self.fill_j += 1

    def traceback(self):
        i, j = len(self.seq1) - 1, len(self.seq2) - 1
        aligned1, aligned2 = [], []
        path = []

        while i > 0 or j > 0:
            path.append((i, j))
            if i > 0 and j > 0 and self.trace[i][j] == '↖':
                aligned1.append(self.seq1[i])
                aligned2.append(self.seq2[j])
                i -= 1
                j -= 1
            elif i > 0 and self.trace[i][j] == '↑':
                aligned1.append(self.seq1[i])
                aligned2.append('-')
                i -= 1
            else:
                aligned1.append('-')
                aligned2.append(self.seq2[j])
                j -= 1
        path.append((0, 0))

        for x, y in path:
            label = self.labels[x][y]
            if label:
                arrow = self.trace[x][y] or ''
                color = "red" if arrow == '↖' else ("blue" if arrow in ['↑', '←'] else "black")
                label.setText(f"<font color='{color}'>{self.dp[x][y]}<br>{arrow}</font>")
                label.setStyleSheet("border: 2px solid black;")

        self.output_label.setText(
            f"Alignment Score: {self.dp[-1][-1]}\n"
            f"Seq1: {''.join(reversed(aligned1))}\n"
            f"Seq2: {''.join(reversed(aligned2))}"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeedlemanWunschVisualizer()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
							QWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPalette, QColor, QFont
import sys

class AssistantGUI(QMainWindow):
	def __init__(self, assistant):
		super().__init__()
		self.assistant = assistant
		self.is_listening = False
		self.initUI()

	def initUI(self):
		# Set window properties
		self.setWindowTitle('Voice Assistant')
		self.setMinimumSize(400, 300)
		
		# Create central widget and layout
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		layout = QVBoxLayout(central_widget)
		
		# Create and style the main button
		self.listen_button = QPushButton('Start Listening')
		self.listen_button.setMinimumSize(200, 200)
		self.listen_button.setFont(QFont('Arial', 14, QFont.Weight.Bold))
		
		# Add drop shadow effect to button
		shadow = QGraphicsDropShadowEffect()
		shadow.setBlurRadius(20)
		shadow.setColor(QColor(0, 0, 0, 150))
		shadow.setOffset(5, 5)
		self.listen_button.setGraphicsEffect(shadow)
		
		# Style the button with 3D effects
		self.listen_button.setStyleSheet("""
			QPushButton {
				background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
												stop:0 #34d399, stop:1 #2ecc71);
				color: white;
				border-radius: 100px;
				border: 4px solid #27ae60;
				padding: 5px;
			}
			QPushButton:hover {
				background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
												stop:0 #3ee6a8, stop:1 #27ae60);
				border: 4px solid #219a52;
			}
			QPushButton:pressed {
				background-color: qlineargradient(x1:0, y1:1, x2:0, y2:0,
												stop:0 #27ae60, stop:1 #219a52);
				border: 4px solid #1e8449;
				padding-left: 7px;
				padding-top: 7px;
			}
		""")
		self.listen_button.clicked.connect(self.toggle_listening)
		
		# Add button to layout with alignment
		layout.addWidget(self.listen_button, alignment=Qt.AlignmentFlag.AlignCenter)
		
		# Set modern dark theme with gradient
		self.setStyleSheet("""
			QMainWindow {
				background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
										  stop:0 #1a202c, stop:1 #2d3748);
			}
			QWidget {
				background: transparent;
			}
		""")

	def toggle_listening(self):
		if not self.is_listening:
			self.listen_button.setText('Stop Listening')
			shadow = QGraphicsDropShadowEffect()
			shadow.setBlurRadius(20)
			shadow.setColor(QColor(0, 0, 0, 150))
			shadow.setOffset(5, 5)
			self.listen_button.setGraphicsEffect(shadow)
			
			self.listen_button.setStyleSheet("""
				QPushButton {
					background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
													stop:0 #f56565, stop:1 #e53e3e);
					color: white;
					border-radius: 100px;
					border: 4px solid #c53030;
					padding: 5px;
				}
				QPushButton:hover {
					background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
													stop:0 #fc8181, stop:1 #f56565);
					border: 4px solid #9b2c2c;
				}
				QPushButton:pressed {
					background-color: qlineargradient(x1:0, y1:1, x2:0, y2:0,
													stop:0 #e53e3e, stop:1 #c53030);
					border: 4px solid #742a2a;
					padding-left: 7px;
					padding-top: 7px;
				}
			""")
			self.assistant.start_listening()
		else:
			self.listen_button.setText('Start Listening')
			shadow = QGraphicsDropShadowEffect()
			shadow.setBlurRadius(20)
			shadow.setColor(QColor(0, 0, 0, 150))
			shadow.setOffset(5, 5)
			self.listen_button.setGraphicsEffect(shadow)
			
			self.listen_button.setStyleSheet("""
				QPushButton {
					background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
													stop:0 #34d399, stop:1 #2ecc71);
					color: white;
					border-radius: 100px;
					border: 4px solid #27ae60;
					padding: 5px;
				}
				QPushButton:hover {
					background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
													stop:0 #3ee6a8, stop:1 #27ae60);
					border: 4px solid #219a52;
				}
				QPushButton:pressed {
					background-color: qlineargradient(x1:0, y1:1, x2:0, y2:0,
													stop:0 #27ae60, stop:1 #219a52);
					border: 4px solid #1e8449;
					padding-left: 7px;
					padding-top: 7px;
				}
			""")
			self.assistant.stop_listening()
		
		self.is_listening = not self.is_listening

def launch_gui(assistant):
	app = QApplication(sys.argv)
	gui = AssistantGUI(assistant)
	gui.show()
	sys.exit(app.exec())
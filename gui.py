from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                               QVBoxLayout, QWidget, QFrame, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QSize, QParallelAnimationGroup, pyqtProperty, QPointF
from PyQt6.QtGui import QColor, QPalette, QFont, QPainter, QRadialGradient, QPainterPath, QAction, QIcon
import sys

class FloatingMessage(QFrame):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        # Create layout with minimal margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add message label with word wrap
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(300)  # Increased from 220 to allow even longer messages
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 10px;
                padding: 8px 12px;
                margin: 0px;
            }
        """)
        self.label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.label)
        
        # Adjust size to content
        self.adjustSize()
        
        # Auto-hide timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        self.timer.start(3000)  # Hide after 3 seconds

class OrbButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)  # Increased size to accommodate animation
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Initialize private variables for properties
        self._glow_intensity = 0
        self._hue_shift = 0
        self._scale_factor = 1.0
        
        # Animation properties
        self.animation_group = QParallelAnimationGroup()
        self.is_listening = False
        self.base_colors = [(46, 171, 255), (255, 94, 247), (59, 255, 247)]  # Blue, Pink, Cyan
        self.current_colors = self.base_colors.copy()

        # Setup animations
        self.setup_animations()
        
        # Animation timer for smooth color transitions
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.setInterval(16)  # ~60 FPS

    def setup_animations(self):
        # Glow animation
        self.glow_anim = QPropertyAnimation(self, b"glowIntensity")
        self.glow_anim.setDuration(2000)
        self.glow_anim.setStartValue(0.0)
        self.glow_anim.setEndValue(1.0)
        self.glow_anim.setLoopCount(-1)
        self.glow_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        # Color shift animation
        self.color_anim = QPropertyAnimation(self, b"hueShift")
        self.color_anim.setDuration(3000)
        self.color_anim.setStartValue(0.0)
        self.color_anim.setEndValue(360.0)
        self.color_anim.setLoopCount(-1)
        
        # Scale animation
        self.scale_anim = QPropertyAnimation(self, b"scaleFactor")
        self.scale_anim.setDuration(1500)
        self.scale_anim.setStartValue(1.0)
        self.scale_anim.setEndValue(1.15)
        self.scale_anim.setLoopCount(-1)
        self.scale_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.animation_group.addAnimation(self.glow_anim)
        self.animation_group.addAnimation(self.color_anim)
        self.animation_group.addAnimation(self.scale_anim)

    def start_animation(self):
        self.is_listening = True
        self.animation_group.start()
        self.animation_timer.start()

    def stop_animation(self):
        self.is_listening = False
        self.animation_group.stop()
        self.animation_timer.stop()
        self._glow_intensity = 0
        self._hue_shift = 0
        self._scale_factor = 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate center and radius
        center = QPointF(self.width() / 2, self.height() / 2)
        base_radius = min(self.width(), self.height()) / 3  # Reduced base size
        radius = base_radius * self._scale_factor

        # Create base gradient for the orb
        gradient = QRadialGradient(center, radius)
        
        if self.is_listening:
            # Shift colors based on hue
            shifted_colors = []
            for color in self.current_colors:
                h = int((color[0] + self._hue_shift) % 360)
                shifted_colors.append((h, color[1], color[2]))
            
            # Add color stops with glow effect
            gradient.setColorAt(0, QColor.fromHsv(int(shifted_colors[0][0]), 200, 255, 255))
            gradient.setColorAt(0.4, QColor.fromHsv(int(shifted_colors[1][0]), 200, 255, 200))
            gradient.setColorAt(0.8, QColor.fromHsv(int(shifted_colors[2][0]), 200, 255, 150))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            # Add outer glow with larger radius
            glow_gradient = QRadialGradient(center, radius * 1.5)
            glow_gradient.setColorAt(0.5, QColor.fromHsv(int(shifted_colors[0][0]), 200, 255, int(100 * self._glow_intensity)))
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            # Draw glow
            painter.setBrush(glow_gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, radius * 1.5, radius * 1.5)
        else:
            # Static appearance when not listening
            gradient.setColorAt(0, QColor(46, 171, 255, 255))
            gradient.setColorAt(0.5, QColor(59, 255, 247, 200))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

        # Draw main orb
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)

    # Property getters/setters for animations
    @pyqtProperty(float)
    def glowIntensity(self):
        return self._glow_intensity
    
    @glowIntensity.setter
    def glowIntensity(self, value):
        self._glow_intensity = value
        self.update()
    
    @pyqtProperty(float)
    def hueShift(self):
        return self._hue_shift
    
    @hueShift.setter
    def hueShift(self, value):
        self._hue_shift = value
        self.update()
    
    @pyqtProperty(float)
    def scaleFactor(self):
        return self._scale_factor
    
    @scaleFactor.setter
    def scaleFactor(self, value):
        self._scale_factor = value
        self.update()

    glow_intensity = property(glowIntensity, glowIntensity)
    hue_shift = property(hueShift, hueShift)
    scale_factor = property(scaleFactor, scaleFactor)

class VoiceAssistantGUI(QMainWindow):
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.current_message = None
        self.initUI()
        
        # Connect assistant signals
        self.assistant.on_speech_detected.connect(self.on_user_speech)
        self.assistant.on_response_ready.connect(self.on_assistant_response)
        self.assistant.on_interim_speech.connect(self.on_interim_speech)
        
    def initUI(self):
        # Create central widget with transparent background
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: transparent;")
        
        # Set window properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create main layout with space for message
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 40, 20, 60)  # Increased bottom margin for orb
        layout.setSpacing(10)  # Add spacing between widgets
        
        # Create message area (invisible placeholder)
        self.message_area = QWidget()
        self.message_area.setMinimumHeight(80)  # Increased message area height
        self.message_area.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.message_area)
        
        # Create close button
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 0.8);
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        close_button.clicked.connect(self.close_application)
        
        # Create orb button
        self.mic_button = OrbButton()
        self.mic_button.clicked.connect(self.toggle_listening)
        
        # Add buttons to layout
        button_layout = QVBoxLayout()
        button_layout.setSpacing(30)  # Increased spacing between close button and orb
        button_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self.mic_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(button_layout)
        
        # Set window size and position
        self.setFixedSize(340, 300)  # Increased width to accommodate wider chat box
        self.move_to_bottom_right()
        
        # Add system tray icon
        self.create_system_tray()

    def create_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icons/app.png"))  # Use your app icon
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.close_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def close_application(self):
        self.tray_icon.hide()
        QApplication.quit()

    def show_message(self, text, is_listening=False, duration=3000):
        # Hide previous message if exists
        if self.current_message and self.current_message.isVisible():
            self.current_message.hide()
            self.current_message.deleteLater()
        
        # Create and show new message
        self.current_message = FloatingMessage(text, self)
        
        # Calculate message position relative to the message area
        message_x = (self.width() - self.current_message.sizeHint().width()) // 2
        message_y = self.message_area.y() + self.message_area.height() - self.current_message.sizeHint().height() - 10
        
        # Ensure message doesn't go above window
        if message_y < 10:
            message_y = 10
        
        # Set position
        self.current_message.move(message_x, message_y)
        self.current_message.show()
        
        # Reset timer for new duration
        self.current_message.timer.stop()
        self.current_message.timer.setInterval(duration)
        self.current_message.timer.start()

    def on_user_speech(self, text):
        self.show_message(f"You: {text}", duration=5000)

    def on_assistant_response(self, text):
        self.show_message(f"Assistant: {text}", duration=5000)

    def on_interim_speech(self, text):
        self.show_message(text, is_listening=True, duration=1500)

    def toggle_listening(self):
        if not self.assistant.is_running:
            self.mic_button.start_animation()
            self.show_message("Listening...", is_listening=True)
            self.assistant.start_listening()
        else:
            self.mic_button.stop_animation()
            self.assistant.stop_listening()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            
    def closeEvent(self, event):
        # Clean up any existing messages
        if self.current_message:
            self.current_message.hide()
            self.current_message.deleteLater()
        super().closeEvent(event)

    def move_to_bottom_right(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20,
                 screen.height() - self.height() - 100)

def launch_gui(assistant):
    app = QApplication(sys.argv)
    gui = VoiceAssistantGUI(assistant)
    gui.show()
    return app, gui
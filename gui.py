import sys
import math
import time
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QEasingCurve, QPropertyAnimation,
    QPointF
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame,
    QSystemTrayIcon, QMenu, QApplication, QPushButton,
    QGraphicsOpacityEffect
)
from PyQt6.QtGui import (
    QColor, QPalette, QFont, QPainter, QRadialGradient, 
    QPainterPath, QAction, QIcon, QBrush, QPixmap
)

class FloatingMessage(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.current_text = text
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 120, 212, 180);
                border-radius: 10px;
                padding: 10px 20px;
                color: white;
                font-size: 12pt;
            }
        """)
        self.setWordWrap(True)
        self.setMinimumWidth(280)  # Set minimum width to prevent narrow messages
        self.setMaximumWidth(300)  # Set maximum width for better readability
        self.update_text(text)
        
        # Create timer for auto-hide
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
        
        # Animation properties
        self.opacity = QGraphicsOpacityEffect(self)
        self.opacity.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity)
        
        # Create fade animation
        self.fade_animation = QPropertyAnimation(self.opacity, b"opacity", self)
        self.fade_animation.setDuration(500)  # 500ms fade duration
        self.fade_animation.finished.connect(self.on_fade_finished)
    
    def update_text(self, text):
        """Update the message text"""
        self.current_text = text
        self.setText(text)
        self.adjustSize()
        
        # Update position to maintain centering
        if self.parent():
            message_x = (self.parent().width() - self.sizeHint().width()) // 2
            message_y = self.parent().message_area.y() + (self.parent().message_area.height() - 
                       self.sizeHint().height()) // 2
            self.move(message_x, message_y)
    
    def fade_out(self):
        """Start the fade out animation"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
    
    def on_fade_finished(self):
        """Called when fade animation is complete"""
        if self.opacity.opacity() == 0:
            self.hide()
            self.deleteLater()
    
    def showEvent(self, event):
        """Override show event to handle fade in"""
        super().showEvent(event)
        self.opacity.setOpacity(1.0)

class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_state = "idle"
        self.current_frame = 0
        self.animation_speed = 50  # milliseconds
        self.max_frames = 60
        
        # Animation parameters
        self.base_radius = 20
        self.wave_amplitude = 5
        self.wave_frequency = 2
        self.color = QColor(0, 120, 212)  # Windows blue
        
        # Enable mouse tracking and set cursor
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Start the animation timer
        self.animation_timer.start(self.animation_speed)
    
    def start_animation(self, state):
        """Start animation with specified state"""
        self.animation_state = state
        if not self.animation_timer.isActive():
            self.animation_timer.start(self.animation_speed)
        self.update()
    
    def update_animation(self):
        """Update animation frame"""
        self.current_frame = (self.current_frame + 1) % self.max_frames
        self.repaint()  # Force immediate repaint
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center point
        center = QPointF(self.width() / 2, self.height() / 2)
        
        if self.animation_state == "idle":
            # Subtle breathing effect for idle state
            scale = 1.0 + 0.05 * math.sin(self.current_frame * 0.1)
            gradient = QRadialGradient(center, self.base_radius * 1.5)
            gradient.setColorAt(0, self.color)
            gradient.setColorAt(0.7, self.color.lighter(120))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, self.base_radius * scale, self.base_radius * scale)
            
        elif self.animation_state == "speaking":
            # More pronounced pulsing effect for speaking
            scale = 1.0 + 0.15 * math.sin(self.current_frame * 0.2)
            gradient = QRadialGradient(center, self.base_radius * 2 * scale)
            gradient.setColorAt(0, self.color)
            gradient.setColorAt(0.6, self.color.lighter(130))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, self.base_radius * scale, self.base_radius * scale)
            
        elif self.animation_state in ["listening", "processing"]:
            # Base orb with glow
            gradient = QRadialGradient(center, self.base_radius * 1.5)
            gradient.setColorAt(0, self.color)
            gradient.setColorAt(0.7, self.color.lighter(120))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, self.base_radius, self.base_radius)
            
            # Animated ripple waves
            for i in range(3):
                wave_offset = (self.current_frame + i * self.max_frames // 3) % self.max_frames
                wave_scale = 1.0 - wave_offset / self.max_frames
                if wave_scale > 0:
                    wave_color = QColor(self.color)
                    wave_color.setAlpha(int(255 * wave_scale * 0.5))
                    wave_gradient = QRadialGradient(center, self.base_radius * (2 + wave_scale))
                    wave_gradient.setColorAt(0.4, wave_color)
                    wave_gradient.setColorAt(1, QColor(0, 0, 0, 0))
                    painter.setBrush(wave_gradient)
                    wave_radius = self.base_radius + (1.0 - wave_scale) * 30
                    painter.drawEllipse(center, wave_radius, wave_radius)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Find the parent VoiceAssistantGUI
            parent = self.parent()
            while parent and not isinstance(parent, VoiceAssistantGUI):
                parent = parent.parent()
            
            if parent:
                parent.toggle_listening()
    
    def enterEvent(self, event):
        # Highlight effect when mouse enters
        self.color = self.color.lighter(110)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # Return to normal color when mouse leaves
        self.color = QColor(0, 120, 212)
        super().leaveEvent(event)

class VoiceAssistantGUI(QMainWindow):
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.is_listening = False
        self.last_activity_time = time.time()
        
        # Create system tray icon with a generated icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Generate a simple icon programmatically
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a gradient circle
        gradient = QRadialGradient(16, 16, 14)
        gradient.setColorAt(0, QColor(0, 120, 212))  # Windows blue
        gradient.setColorAt(1, QColor(0, 100, 180))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        
        # Set the generated icon
        self.tray_icon.setIcon(QIcon(pixmap))
        self.setWindowIcon(QIcon(pixmap))
        
        self.current_message = None
        self.initUI()
        
        # Create auto-close timer
        self.inactivity_timer = QTimer()
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(1000)  # Check every second
        
        # Connect assistant signals
        self.setup_signal_connections()
    
    def setup_signal_connections(self):
        """Set up signal connections with the assistant"""
        if hasattr(self.assistant, 'on_speech_detected'):
            self.assistant.on_speech_detected.connect(self.on_user_speech)
        if hasattr(self.assistant, 'on_response_ready'):
            self.assistant.on_response_ready.connect(self.on_assistant_response)
        if hasattr(self.assistant, 'on_interim_speech'):
            self.assistant.on_interim_speech.connect(self.on_interim_speech)
        if hasattr(self.assistant, 'on_assistant_word'):
            self.assistant.on_assistant_word.connect(self.on_assistant_word)
    
    def on_user_speech(self, text):
        """Handle detected user speech"""
        # Clear any existing assistant message
        if self.current_message:
            self.current_message.fade_out()
            self.current_message = None
        
        # Show user's message
        self.show_message(f"You: {text}", is_listening=True)
    
    def on_assistant_response(self, response):
        """Handle assistant's response"""
        # Clear user's message first
        if self.current_message:
            self.current_message.fade_out()
            self.current_message = None
        
        # Show assistant's response
        self.show_message(f"Athena: {response}")
    
    def on_assistant_word(self, word):
        """Handle word-by-word assistant response"""
        # If there's a user message showing, clear it
        if self.current_message and self.current_message.current_text.startswith("You:"):
            self.current_message.fade_out()
            self.current_message = None
        
        # Start or continue assistant message
        if not self.current_message:
            self.current_message = FloatingMessage("Athena: " + word, self)
            # Position message above the orb
            message_x = (self.width() - self.current_message.sizeHint().width()) // 2
            message_y = self.message_area.y() + (self.message_area.height() - 
                       self.current_message.sizeHint().height()) // 2
            self.current_message.move(message_x, message_y)
            self.current_message.show()
        else:
            # Append new word to existing message
            self.current_message.update_text(self.current_message.current_text + " " + word)
        
        # Reset the timer with longer duration
        self.current_message.timer.stop()
        self.current_message.timer.setInterval(8000)  # 8 seconds
        self.current_message.timer.start()
    
    def on_interim_speech(self, text):
        """Handle interim speech results"""
        if self.current_message:
            self.current_message.update_text(text)
    
    def show_message(self, text, is_listening=False):
        """Show a floating message"""
        # Remove existing message if any
        if self.current_message:
            self.current_message.fade_out()
        
        # Create new message
        self.current_message = FloatingMessage(text, self)
        
        # Position message above the orb
        message_x = (self.width() - self.current_message.sizeHint().width()) // 2
        message_y = self.message_area.y() + (self.message_area.height() - 
                   self.current_message.sizeHint().height()) // 2
        
        self.current_message.move(message_x, message_y)
        self.current_message.show()
        
        # Start auto-hide timer if not in listening mode
        if not is_listening:
            self.current_message.timer.setInterval(8000)  # 8 seconds
            self.current_message.timer.start()
    
    def start_response(self, text):
        """Start a new response message"""
        if self.current_message:
            self.current_message.fade_out()
            self.current_message = None
        
        self.current_message = FloatingMessage(text, self)
        
        # Position message above the orb
        message_x = (self.width() - self.current_message.sizeHint().width()) // 2
        message_y = self.message_area.y() + (self.message_area.height() - 
                   self.current_message.sizeHint().height()) // 2
        
        self.current_message.move(message_x, message_y)
        self.current_message.show()
        
        # Start timer with longer duration for responses
        self.current_message.timer.setInterval(8000)  # 8 seconds for better readability
        self.current_message.timer.start()
        
    def on_assistant_speaking(self):
        """Called when the assistant starts speaking"""
        self.orb_widget.start_animation("speaking")
        
    def on_assistant_listening(self):
        """Called when the assistant starts listening"""
        self.orb_widget.start_animation("listening")
        
    def on_assistant_processing(self):
        """Called when the assistant is processing"""
        self.orb_widget.start_animation("processing")
        
    def on_assistant_idle(self):
        """Called when the assistant becomes idle"""
        self.orb_widget.start_animation("idle")

    def initUI(self):
        self.setWindowTitle("Athena Voice Assistant")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Message area (invisible placeholder for proper spacing)
        self.message_area = QWidget()
        self.message_area.setMinimumHeight(80)
        self.message_area.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.message_area)
        
        # Create orb widget
        self.orb_widget = OrbWidget()
        self.orb_widget.setFixedSize(100, 100)
        layout.addWidget(self.orb_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Set window size and position
        self.setFixedSize(340, 300)
        
        # Create system tray
        self.create_system_tray()
        
        # Move to bottom right
        self.move_to_bottom_right()
    
    def check_inactivity(self):
        """Check for inactivity and hide window if inactive for too long"""
        if not self.is_listening and time.time() - self.last_activity_time > 10:
            self.hide()
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self.last_activity_time = time.time()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
        self.last_activity_time = time.time()
    
    def enterEvent(self, event):
        """Handle mouse enter events"""
        super().enterEvent(event)
        self.last_activity_time = time.time()
    
    def leaveEvent(self, event):
        """Handle mouse leave events"""
        super().leaveEvent(event)
        self.last_activity_time = time.time()

    def create_system_tray(self):
        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show_and_activate)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def show_and_activate(self):
        """Show and activate the window"""
        self.show()
        self.activateWindow()
        self.last_activity_time = time.time()
    
    def move_to_bottom_right(self):
        """Position the window in the bottom right of the screen"""
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20,
                 screen.height() - self.height() - 100)
    
    def toggle_listening(self):
        """Toggle between listening and idle states"""
        self.is_listening = not self.is_listening
        if self.is_listening:
            # Start voice recognition
            self.assistant.start_listening()
        else:
            self.assistant.stop_listening()
            self.orb_widget.start_animation("idle")

    def closeEvent(self, event):
        # Clean up any existing messages
        if self.current_message:
            self.current_message.fade_out()
            self.current_message = None
        super().closeEvent(event)

def launch_gui(assistant):
    app = QApplication(sys.argv)
    gui = VoiceAssistantGUI(assistant)
    gui.show()
    return app, gui
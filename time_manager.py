from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication
import datetime
import re
from typing import Dict, Tuple

class TimeManager(QObject):
    timer_complete = pyqtSignal(str)  # Emits timer name when complete
    alarm_triggered = pyqtSignal(str)  # Emits alarm name when triggered
    
    def __init__(self):
        super().__init__()
        self.timers: Dict[str, QTimer] = {}
        self.alarms: Dict[str, Tuple[datetime.time, QTimer]] = {}
        
        # Ensure we're in the main thread
        if QThread.currentThread() != QApplication.instance().thread():
            raise RuntimeError("TimeManager must be created in the main thread")
        
        # Start checking alarms every minute
        self.alarm_checker = QTimer()
        self.alarm_checker.timeout.connect(self._check_alarms)
        self.alarm_checker.start(60000)  # Check every minute
    
    def set_timer(self, duration_str: str) -> str:
        """Set a timer for the specified duration"""
        try:
            # Parse duration string (e.g., "2 minutes", "1 hour 30 minutes", "45 seconds")
            minutes = 0
            hours = 0
            seconds = 0
            
            # Extract hours
            hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)', duration_str.lower())
            if hour_match:
                hours = int(hour_match.group(1))
            
            # Extract minutes
            min_match = re.search(r'(\d+)\s*(?:minute|min|m(?!\s*s))', duration_str.lower())
            if min_match:
                minutes = int(min_match.group(1))
            
            # Extract seconds
            sec_match = re.search(r'(\d+)\s*(?:second|sec|s)', duration_str.lower())
            if sec_match:
                seconds = int(sec_match.group(1))
            
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
            if total_ms <= 0:
                return "Please specify a valid duration"
            
            # Create timer name
            timer_name = f"Timer_{len(self.timers) + 1}"
            
            # Create and start timer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._timer_complete(timer_name))
            timer.start(total_ms)
            
            # Store timer
            self.timers[timer_name] = timer
            
            # Format response message
            time_parts = []
            if hours > 0:
                time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if seconds > 0:
                time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
            duration_str = " and ".join(time_parts) if len(time_parts) > 1 else time_parts[0]
            return f"Timer set for {duration_str}"
            
        except Exception as e:
            return f"Error setting timer: {str(e)}"
    
    def set_alarm(self, time_str: str) -> str:
        """Set an alarm for the specified time"""
        try:
            # Try to parse time string (e.g., "7:30", "15:45", "7:30 AM", "3:45 PM")
            time_formats = ["%H:%M", "%I:%M %p", "%I:%M%p"]
            alarm_time = None
            
            for fmt in time_formats:
                try:
                    alarm_time = datetime.datetime.strptime(time_str.strip(), fmt).time()
                    break
                except ValueError:
                    continue
            
            if not alarm_time:
                return "Please specify a valid time (e.g., '7:30', '15:45', '7:30 AM')"
            
            # Calculate time until alarm
            now = datetime.datetime.now()
            alarm_datetime = datetime.datetime.combine(now.date(), alarm_time)
            
            # If alarm time is earlier today, set for tomorrow
            if alarm_datetime <= now:
                alarm_datetime += datetime.timedelta(days=1)
            
            ms_until_alarm = int((alarm_datetime - now).total_seconds() * 1000)
            
            # Create alarm name
            alarm_name = f"Alarm_{len(self.alarms) + 1}"
            
            # Create and start timer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._alarm_triggered(alarm_name))
            timer.start(ms_until_alarm)
            
            # Store alarm
            self.alarms[alarm_name] = (alarm_time, timer)
            
            return f"Alarm set for {alarm_time.strftime('%I:%M %p')}"
            
        except Exception as e:
            return f"Error setting alarm: {str(e)}"
    
    def cancel_timer(self, timer_name: str) -> str:
        """Cancel a specific timer"""
        if timer_name in self.timers:
            self.timers[timer_name].stop()
            del self.timers[timer_name]
            return f"Cancelled {timer_name}"
        return "Timer not found"
    
    def cancel_alarm(self, alarm_name: str) -> str:
        """Cancel a specific alarm"""
        if alarm_name in self.alarms:
            self.alarms[alarm_name][1].stop()
            del self.alarms[alarm_name]
            return f"Cancelled {alarm_name}"
        return "Alarm not found"
    
    def list_timers(self) -> str:
        """List all active timers"""
        if not self.timers:
            return "No active timers"
        return "Active timers: " + ", ".join(self.timers.keys())
    
    def list_alarms(self) -> str:
        """List all active alarms"""
        if not self.alarms:
            return "No active alarms"
        alarm_list = [f"{name} ({time[0].strftime('%I:%M %p')})" for name, time in self.alarms.items()]
        return "Active alarms: " + ", ".join(alarm_list)
    
    def _timer_complete(self, timer_name: str):
        """Internal method called when a timer completes"""
        if timer_name in self.timers:
            self.timer_complete.emit(timer_name)
            del self.timers[timer_name]
    
    def _alarm_triggered(self, alarm_name: str):
        """Internal method called when an alarm is triggered"""
        if alarm_name in self.alarms:
            self.alarm_triggered.emit(alarm_name)
            del self.alarms[alarm_name]
    
    def _check_alarms(self):
        """Check if any alarms need to be triggered (backup check)"""
        now = datetime.datetime.now().time()
        for alarm_name, (alarm_time, timer) in list(self.alarms.items()):
            if alarm_time <= now:
                self._alarm_triggered(alarm_name)

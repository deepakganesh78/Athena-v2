from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt
from audio_manager import AudioManager
from system_controller import SystemController
from web_search import WebSearch
from time_manager import TimeManager
from gui import VoiceAssistantGUI
import time
import random
import sys
import threading
import nltk
from nltk.stem import WordNetLemmatizer
import re
from difflib import SequenceMatcher
from datetime import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from voice_recognition import VoiceRecognizer
import speech_recognition as sr

# Attempt to handle DPI awareness
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception as e:
    print(f"DPI awareness setting failed: {e}")

class VoiceAssistant(QObject):
    on_speech_detected = pyqtSignal(str)
    on_command_processing = pyqtSignal()
    on_response_ready = pyqtSignal(str)
    on_interim_speech = pyqtSignal(str)
    on_assistant_speaking = pyqtSignal(str)
    on_assistant_word = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.voice_recognizer = VoiceRecognizer()
        self.audio_manager = AudioManager()
        self.system_controller = SystemController()
        self.web_search = WebSearch()
        self.is_running = False
        self.listen_thread = None
        self.lemmatizer = WordNetLemmatizer()
        self.time_manager = None  # Will be set by GUI
        self.gui = None  # Will be set by set_gui method
        self.recognizer = sr.Recognizer()
        self.listening = False
        
        # Connect signals
        self.audio_manager.on_word_spoken.connect(self.on_word_spoken)
        self.audio_manager.on_speaking_started.connect(self.on_speaking_started)
        self.audio_manager.on_speaking_finished.connect(self.on_speaking_finished)
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger')

        # Initialize command patterns
        self.command_patterns = {
            'volume': {
                'patterns': [
                    r'(?:turn|set|make|adjust|change).*(?:volume|sound).*(?:up|down|to|higher|lower)',
                    r'(?:increase|decrease|raise|lower).*(?:volume|sound)',
                    r'(?:louder|softer|quieter)',
                    r'(?:volume|sound).*(?:up|down|higher|lower)',
                    r'(?:mute|unmute).*(?:volume|sound|speaker)?',
                    r'set.*(?:volume|sound).*to.*(\d+)(?:\s*percent)?',
                    r'(?:volume|sound).*(\d+)(?:\s*percent)?',
                    r'(?:make|adjust).*(?:volume|sound).*(\d+)(?:\s*percent)?'
                ],
                'keywords': ['volume', 'sound', 'loud', 'quiet', 'increase', 'decrease', 'mute', 'unmute', 'percent'],
                'synonyms': {
                    'up': ['increase', 'raise', 'higher', 'louder', 'boost', 'amplify'],
                    'down': ['decrease', 'lower', 'quieter', 'softer', 'reduce', 'diminish'],
                    'mute': ['silence', 'quiet', 'disable sound'],
                    'unmute': ['enable sound', 'restore sound']
                }
            },
            'time': {
                'patterns': [
                    r'^(?:what|tell|give).*(?:time|clock)(?:\s+is\s+it)?$',
                    r'^(?:current|present).*time$',
                    r'^(?:what time is it|got the time)$',
                ],
                'keywords': ['time', 'clock', 'hour', 'minute'],
                'synonyms': {
                    'time': ['clock', 'hour', 'moment', 'current time'],
                }
            },
            'greeting': {
                'patterns': [
                    r'(?:hello|hi|hey|greetings|good).*(?:morning|afternoon|evening)?',
                    r'(?:how are|how\'re) you',
                    r'(?:nice to meet you|pleased to meet you)',
                ],
                'keywords': ['hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening'],
                'synonyms': {
                    'hello': ['hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
                    'how are you': ['how you doing', 'how\'s it going', 'what\'s up']
                }
            },
            'open_app': {
                'patterns': [
                    r'(?:open|launch|start|run)\s+(.+)',
                    r'(?:can you )?(?:open|launch|start|run)\s+(.+)',
                ],
                'handler': self.handle_open_app
            },
            'close_app': {
                'patterns': [
                    r'(?:close|quit|exit|terminate|end)\s+(.+)',
                    r'(?:can you )?(?:close|quit|exit|terminate|end)\s+(.+)',
                ],
                'handler': self.handle_close_app
            },
            'system_control': {
                'patterns': [
                    r'(?:shutdown|turn off|power off).*(?:computer|system|pc)',
                    r'(?:restart|reboot).*(?:computer|system|pc)',
                    r'(?:sleep|hibernate).*(?:computer|system|pc)',
                    r'(?:can you|could you|please).*(?:shutdown|restart|reboot).*(?:computer|system|pc)',
                ],
                'keywords': ['shutdown', 'restart', 'reboot', 'power', 'sleep', 'hibernate'],
                'synonyms': {
                    'shutdown': ['turn off', 'power off', 'shut down', 'switch off'],
                    'restart': ['reboot', 'reset', 'reload', 'relaunch'],
                    'sleep': ['hibernate', 'suspend', 'standby']
                }
            },
            'search': {
                'patterns': [
                    r'(?:search|look up|find|google|tell me about).*',
                    r'(?:what|who|which|when|where|why|how).*(?:is|are|was|were|will|do|does|did).*',
                    r'(?:latest|best|top|newest|recent).*(?:movies|news|games|shows|music|books).*',
                    r'(?:can you|could you|please).*(?:search|look up|find|tell).*',
                ],
                'keywords': ['search', 'look up', 'find', 'what is', 'who is', 'tell me', 'best', 'latest'],
                'synonyms': {
                    'search': ['look up', 'find', 'google', 'research', 'investigate'],
                    'what is': ['tell me about', 'explain', 'describe']
                }
            },
            'weather': {
                'patterns': [
                    r'(?:what\'s|what is|how\'s).*(?:weather|temperature|forecast)',
                    r'(?:will it|is it going to).*(?:rain|snow|be sunny)',
                    r'(?:temperature|weather).*(?:today|tomorrow|this week)',
                ],
                'keywords': ['weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny'],
                'synonyms': {
                    'weather': ['temperature', 'climate', 'conditions'],
                    'forecast': ['prediction', 'outlook', 'weather report']
                }
            },
            'reminder': {
                'patterns': [
                    r'(?:remind|remember|notification).*(?:me|to)\\s+([\\w\\s]+)',
                    r'(?:set|create).*(?:reminder|alarm).*(?:for|to)\\s+([\\w\\s]+)',
                    r'(?:don\'t let me forget|help me remember)\\s+([\\w\\s]+)',
                ],
                'keywords': ['remind', 'reminder', 'alarm', 'notification', 'remember'],
                'synonyms': {
                    'remind': ['remember', 'notify', 'alert'],
                    'reminder': ['notification', 'alert', 'alarm']
                }
            },
            'date': {
                'patterns': [
                    r'what (?:is|\'s) (?:today\'s )?(?:date|day)',
                    r'what (?:date|day) is (?:it|today)',
                    r'tell me (?:the )?(?:date|day)',
                    r'what (?:is|\'s) the (?:date|day)(?: today)?',
                    r'current (?:date|day)'
                ],
                'keywords': ['date', 'day', 'today', 'current'],
                'synonyms': {
                    'date': ['day', 'today'],
                    'tell': ['show', 'give', 'what is']
                }
            },
            'timer': {
                'patterns': [
                    r'(?:set|start|create)\s+(?:a\s+)?timer\s+(?:for\s+)?(.+)',
                    r'(?:give|set)\s+me\s+(?:a\s+)?timer\s+(?:for\s+)?(.+)',
                ],
                'handler': self.handle_timer_command
            },
            'alarm': {
                'patterns': [
                    r'(?:set|create)\s+(?:an\s+)?alarm\s+(?:for\s+)?(.+)',
                    r'wake\s+me\s+(?:up\s+)?(?:at\s+)?(.+)',
                ],
                'handler': self.handle_alarm_command
            },
            'cancel_timer': {
                'patterns': [
                    r'(?:cancel|stop|remove)\s+(?:the\s+)?timer',
                    r'(?:cancel|stop|remove)\s+(?:all\s+)?timers',
                ],
                'handler': self.handle_cancel_timer
            },
            'cancel_alarm': {
                'patterns': [
                    r'(?:cancel|stop|remove)\s+(?:the\s+)?alarm',
                    r'(?:cancel|stop|remove)\s+(?:all\s+)?alarms',
                ],
                'handler': self.handle_cancel_alarm
            },
            'list_timers': {
                'patterns': [
                    r'(?:list|show|what are)\s+(?:the\s+)?(?:active\s+)?timers',
                    r'(?:how many|what)\s+timers\s+(?:do I have|are running)',
                ],
                'handler': self.handle_list_timers
            },
            'list_alarms': {
                'patterns': [
                    r'(?:list|show|what are)\s+(?:the\s+)?(?:active\s+)?alarms',
                    r'(?:how many|what)\s+alarms\s+(?:do I have|are set)',
                ],
                'handler': self.handle_list_alarms
            },
        }
        
        # Initialize previous command type for context
        self.previous_command_type = None
        
    def get_command_similarity(self, text, pattern):
        return SequenceMatcher(None, text.lower(), pattern.lower()).ratio()

    def get_word_synonyms(self, word):
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().lower())
        return synonyms

    def extract_number(self, text):
        # Extract numeric values from text
        numbers = re.findall(r'\b(\d+)\b', text)
        if numbers:
            return int(numbers[0])
        
        # Handle word numbers
        word_to_num = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'twenty': 20, 'thirty': 30, 'forty': 40,
            'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80,
            'ninety': 90, 'hundred': 100
        }
        
        words = text.lower().split()
        for word in words:
            if word in word_to_num:
                return word_to_num[word]
        
        return None

    def identify_command_type(self, text):
        text = text.lower()
        best_match = None
        highest_score = 0
        
        # Tokenize and lemmatize input text
        tokens = word_tokenize(text)
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        lemmatized_text = ' '.join(lemmatized_tokens)
        
        # Store context of previous commands for better understanding
        context_bonus = 0.1  # Bonus score for commands related to previous context
        
        for cmd_type, cmd_info in self.command_patterns.items():
            # Check patterns with regex
            for pattern in cmd_info['patterns']:
                if re.search(pattern, lemmatized_text, re.IGNORECASE):
                    return cmd_type, 1.0
            
            # Initialize score for this command type
            score = 0
            
            # Check direct keyword matches
            keyword_matches = sum(1 for keyword in cmd_info['keywords'] if keyword in lemmatized_text)
            if keyword_matches > 0:
                score += 0.4 * (keyword_matches / len(cmd_info['keywords']))
            
            # Check for synonyms using WordNet
            for keyword in cmd_info['keywords']:
                keyword_synonyms = self.get_word_synonyms(keyword)
                synonym_matches = sum(1 for syn in keyword_synonyms if syn in lemmatized_text)
                if synonym_matches > 0:
                    score += 0.3 * (synonym_matches / len(keyword_synonyms))
            
            # Check command-specific synonyms
            for syn_key, syn_values in cmd_info.get('synonyms', {}).items():
                syn_matches = sum(1 for syn in syn_values if syn in lemmatized_text)
                if syn_matches > 0:
                    score += 0.3 * (syn_matches / len(syn_values))
            
            # Apply context bonus if the command is related to previous ones
            if hasattr(self, 'previous_command_type') and self.previous_command_type == cmd_type:
                score += context_bonus
            
            # Update best match if this score is higher
            if score > highest_score:
                highest_score = score
                best_match = cmd_type
        
        # Store this command type for future context
        if highest_score > 0.3:
            self.previous_command_type = best_match
        
        return best_match, highest_score if highest_score > 0.3 else (None, 0)

    def get_current_date(self):
        """Get current date in a natural format"""
        today = datetime.now()
        # Get day with proper ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
        day = today.day
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        return today.strftime(f"%A, %B {day}{suffix}, %Y")

    def get_day_name(self):
        """Get current day name"""
        return datetime.now().strftime("%A")

    def process_command(self, command):
        if not command:
            print("Skipping command processing - no command received")
            return

        print(f"Processing command: '{command}'")
        self.on_command_processing.emit()
        self.on_speech_detected.emit(command)

        # First check for app opening commands as they're most direct
        for cmd_type in ['open_app', 'close_app']:
            for pattern in self.command_patterns[cmd_type]['patterns']:
                matches = re.findall(pattern, command.lower())
                if matches:
                    return self.command_patterns[cmd_type]['handler'](command, matches)
        
        # Then check other command types
        # Identify command type and confidence
        cmd_type, confidence = self.identify_command_type(command)
        
        if cmd_type == 'volume':
            # Check for numeric volume setting
            volume_match = re.search(r'(\d+)(?:\s*percent)?', command)
            if volume_match:
                volume_level = int(volume_match.group(1))
                # Ensure volume is between 0 and 100
                volume_level = max(0, min(100, volume_level))
                self.audio_manager.set_volume(volume_level / 100.0)
                self.respond(f"Setting volume to {volume_level} percent")
            else:
                # Handle relative volume changes
                if any(word in command.lower() for word in ['up', 'higher', 'increase', 'louder', 'raise']):
                    self.audio_manager.volume_up()
                    self.respond("Increasing volume")
                elif any(word in command.lower() for word in ['down', 'lower', 'decrease', 'quieter', 'softer']):
                    self.audio_manager.volume_down()
                    self.respond("Decreasing volume")
                elif any(word in command.lower() for word in ['mute', 'silence']):
                    self.audio_manager.mute()
                    self.respond("Muting volume")
                elif any(word in command.lower() for word in ['unmute', 'restore']):
                    self.audio_manager.unmute()
                    self.respond("Unmuting volume")
        elif cmd_type == 'time':
            current_time = time.strftime("%I:%M %p")
            self.respond(f"The current time is {current_time}")
        elif cmd_type == 'greeting':
            responses = [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Hey! I'm here to help!",
                "Greetings! How may I assist you?",
                "Good to see you! What's on your mind?"
            ]
            self.respond(random.choice(responses))
        elif cmd_type == 'search':
            search_query = re.sub(r'(?:search|look up|find|google|for|please|could you|can you|what is|who is|tell me about)\\s+', '', command).strip()
            
            # For definition questions, don't announce the search
            if any(phrase in command.lower() for phrase in ['what is', 'what are', 'define', 'tell me about']):
                result = self.web_search.get_information(command)
                self.respond(result)
            else:
                # For general searches, keep the announcement
                self.respond(f"Searching for information about {search_query}")
                result = self.web_search.get_information(command)
                self.respond(result)
        elif cmd_type == 'weather':
            self.respond("Let me check the current weather")
            result = self.web_search.get_information(f"current weather forecast {time.strftime('%Y-%m-%d')}")
            self.respond(result)
        elif cmd_type == 'reminder':
            reminder_text = re.sub(r'(?:remind|remember|notification|me|to|set|create|reminder|alarm|for|don\'t let me forget|help me remember)\\s+', '', command).strip()
            self.respond(f"I'll remind you to {reminder_text}")
            # TODO: Implement reminder functionality
        elif cmd_type == 'date':
            if any(phrase in command.lower() for phrase in [
                'what is today\'s date', 'what date is it', 
                'what is the date', 'tell me the date'
            ]):
                current_date = self.get_current_date()
                self.respond(f"Today is {current_date}")
                return
            elif any(phrase in command.lower() for phrase in [
                'what day is it', 'what is the day', 
                'what day is today', 'what is the day today',
                'tell me the day', 'what\'s today'
            ]):
                day_name = self.get_day_name()
                self.respond(f"Today is {day_name}")
                return
            else:
                current_date = self.get_current_date()
                self.respond(f"The current date is {current_date}")
        elif cmd_type == 'timer':
            # Check for numeric volume setting
            duration_match = re.search(r'(\d+)(?:\s*(?:minutes|minute|mins|min|m|seconds|second|secs|sec|s|h|hours|hour))?', command)
            if duration_match:
                duration = duration_match.group(1)
                unit = duration_match.group(2)
                if unit in ['minutes', 'minute', 'mins', 'min', 'm']:
                    duration_in_seconds = int(duration) * 60
                elif unit in ['seconds', 'second', 'secs', 'sec', 's']:
                    duration_in_seconds = int(duration)
                elif unit in ['hours', 'hour', 'h']:
                    duration_in_seconds = int(duration) * 3600
                else:
                    duration_in_seconds = int(duration) * 60  # Default to minutes
                response = self.time_manager.set_timer(duration_in_seconds)
                self.audio_manager.speak(response)
                return
        elif cmd_type == 'alarm':
            time_str = re.sub(r'(?:set|create|wake|me|up|at|alarm|for)\\s+', '', command).strip()
            response = self.time_manager.set_alarm(time_str)
            self.audio_manager.speak(response)
            return
        elif cmd_type == 'cancel_timer':
            response = self.time_manager.list_timers()
            if response == "No active timers":
                self.audio_manager.speak(response)
            else:
                # Cancel all timers for now - could be made more specific later
                for timer_name in list(self.time_manager.timers.keys()):
                    self.time_manager.cancel_timer(timer_name)
                self.audio_manager.speak("All timers cancelled")
            return
        elif cmd_type == 'cancel_alarm':
            response = self.time_manager.list_alarms()
            if response == "No active alarms":
                self.audio_manager.speak(response)
            else:
                # Cancel all alarms for now - could be made more specific later
                for alarm_name in list(self.time_manager.alarms.keys()):
                    self.time_manager.cancel_alarm(alarm_name)
                self.audio_manager.speak("All alarms cancelled")
            return
        elif cmd_type == 'list_timers':
            response = self.time_manager.list_timers()
            self.audio_manager.speak(response)
            return
        elif cmd_type == 'list_alarms':
            response = self.time_manager.list_alarms()
            self.audio_manager.speak(response)
            return
        else:
            # For any unrecognized command, try to find relevant information
            self.respond("Let me search for that information")
            result = self.web_search.get_information(command)
            self.respond(result)

    def handle_open_app(self, command, matches):
        """Handle requests to open applications"""
        app_name = matches[0].strip().lower()
        
        # Remove common phrases
        app_name = re.sub(r'(?:please|for me|the app|application)\s*', '', app_name)
        
        # Try to open the application
        response = self.system_controller.open_application(app_name)
        self.audio_manager.speak(response)
        return True

    def handle_close_app(self, command, matches):
        """Handle requests to close applications"""
        app_name = matches[0].strip().lower()
        
        # Remove common phrases
        app_name = re.sub(r'(?:please|for me|the app|application)\s*', '', app_name)
        
        # Try to close the application
        response = self.system_controller.close_application(app_name)
        self.audio_manager.speak(response)
        return True

    def handle_timer_command(self, command, matches):
        """Handle timer-related commands"""
        duration = matches[0].strip()
        response = self.time_manager.set_timer(duration)
        self.audio_manager.speak(response)
        return True
    
    def handle_alarm_command(self, command, matches):
        """Handle alarm-related commands"""
        time_str = matches[0].strip()
        response = self.time_manager.set_alarm(time_str)
        self.audio_manager.speak(response)
        return True
    
    def handle_cancel_timer(self, command, matches):
        """Handle timer cancellation"""
        response = self.time_manager.list_timers()
        if response == "No active timers":
            self.audio_manager.speak(response)
        else:
            # Cancel all timers for now - could be made more specific later
            for timer_name in list(self.time_manager.timers.keys()):
                self.time_manager.cancel_timer(timer_name)
            self.audio_manager.speak("All timers cancelled")
        return True
    
    def handle_cancel_alarm(self, command, matches):
        """Handle alarm cancellation"""
        response = self.time_manager.list_alarms()
        if response == "No active alarms":
            self.audio_manager.speak(response)
        else:
            # Cancel all alarms for now - could be made more specific later
            for alarm_name in list(self.time_manager.alarms.keys()):
                self.time_manager.cancel_alarm(alarm_name)
            self.audio_manager.speak("All alarms cancelled")
        return True
    
    def handle_list_timers(self, command, matches):
        """Handle timer listing"""
        response = self.time_manager.list_timers()
        self.audio_manager.speak(response)
        return True
    
    def handle_list_alarms(self, command, matches):
        """Handle alarm listing"""
        response = self.time_manager.list_alarms()
        self.audio_manager.speak(response)
        return True
    
    def _on_timer_complete(self, timer_name):
        """Handle timer completion"""
        self.audio_manager.speak(f"{timer_name} is complete!")
    
    def _on_alarm_triggered(self, alarm_name):
        """Handle alarm triggering"""
        self.audio_manager.speak(f"Wake up! {alarm_name} is ringing!")
    
    def handle_volume_command(self, command):
        command = command.lower()
        
        # Check for specific volume level
        if "set" in command or "to" in command:
            number = self.extract_number(command)
            if number is not None:
                self.audio_manager.set_volume(number)
                responses = [
                    f"I've set the volume to {number} percent for you",
                    f"Alright, volume is now at {number} percent",
                    f"Done! Volume adjusted to {number} percent"
                ]
                self.respond(random.choice(responses))
                return
        
        # Check for volume increase
        if any(word in command for word in ['up', 'higher', 'increase', 'louder', 'raise']):
            self.audio_manager.change_volume(10)
            responses = [
                "I've turned up the volume a bit",
                "Volume's going up",
                "Making it a bit louder for you"
            ]
            self.respond(random.choice(responses))
            return
        
        # Check for volume decrease
        if any(word in command.lower() for word in ['down', 'lower', 'decrease', 'quieter', 'softer']):
            self.audio_manager.change_volume(-10)
            responses = [
                "I've lowered the volume for you",
                "Volume's going down",
                "Making it a bit quieter"
            ]
            self.respond(random.choice(responses))
            return
        
        self.respond("I'm not sure what you want me to do with the volume. Could you be more specific?")

    def respond(self, message):
        print(f"Assistant response: {message}")
        self.audio_manager.speak(message)
        self.on_response_ready.emit(message)

    def handle_start_speaking(self, text):
        self.on_assistant_speaking.emit("Assistant: " + text)

    def handle_word_spoken(self, word):
        self.on_assistant_word.emit(word)

    def handle_end_speaking(self):
        pass  # We can use this if needed

    def start_listening(self):
        """Start listening for voice input"""
        if not self.listen_thread or not self.listen_thread.is_alive():
            self.listening = True
            self.gui.on_assistant_listening()
            self.listen_thread = threading.Thread(target=self._listen_loop)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            
    def stop_listening(self):
        """Stop listening for voice input"""
        self.listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)
        self.gui.on_assistant_idle()

    def _cleanup_listen_thread(self):
        """Helper method to cleanup the listening thread"""
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)  # Wait for max 1 second
            if self.listen_thread.is_alive():
                print("Warning: Listen thread is taking longer than expected to stop")

    def _listen_loop(self):
        """Main listening loop"""
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone initialized successfully")
            
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            self.gui.on_assistant_processing()
                            print(f"Recognized: {text}")
                            self.process_command(text)
                    except sr.UnknownValueError:
                        pass  # Speech was not understood
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                except sr.WaitTimeoutError:
                    pass  # No speech detected within timeout
                except Exception as e:
                    print(f"Error in listening loop: {e}")
                    
    def handle_partial_result(self, text):
        self.on_interim_speech.emit(f"Listening: {text}")

    def on_word_spoken(self, word):
        self.on_assistant_word.emit(word)

    def on_speaking_started(self):
        """Called when the assistant starts speaking"""
        self.gui.on_assistant_speaking()
        
    def on_speaking_finished(self):
        """Called when the assistant finishes speaking"""
        self.gui.on_assistant_idle()

    def set_gui(self, gui):
        """Set the GUI reference"""
        self.gui = gui

def main():
    # Create QApplication first
    app = QApplication(sys.argv)
    
    # Enable High DPI scaling for PyQt6
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create the assistant and GUI
    assistant = VoiceAssistant()
    gui = VoiceAssistantGUI(assistant)
    
    # Set up bidirectional reference
    assistant.set_gui(gui)
    
    # Create TimeManager in the main thread
    time_manager = TimeManager()
    assistant.time_manager = time_manager
    
    # Connect time manager signals
    time_manager.timer_complete.connect(assistant._on_timer_complete)
    time_manager.alarm_triggered.connect(assistant._on_alarm_triggered)
    
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

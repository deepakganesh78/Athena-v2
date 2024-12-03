from voice_recognition import VoiceRecognizer
from audio_manager import AudioManager
from system_controller import SystemController
from web_search import WebSearch
import time
import random
from PyQt6.QtCore import QObject, pyqtSignal
from gui import launch_gui
import threading
import re
from difflib import SequenceMatcher
from datetime import datetime
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import sys

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
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt')
            nltk.download('wordnet')
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
                    r'(?:open|launch|start|run).*(?:application|app|program)',
                    r'(?:open|launch|start|run)\\s+([\\w\\s]+)',
                    r'(?:can you|could you|please).*(?:open|launch|start|run)\\s+([\\w\\s]+)',
                ],
                'keywords': ['open', 'launch', 'start', 'run', 'application', 'program'],
                'synonyms': {
                    'open': ['launch', 'start', 'run', 'execute', 'begin', 'initiate'],
                    'application': ['app', 'program', 'software']
                }
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
        numbers = re.findall(r'\\b(\d+)\\b', text)
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
            for syn_key, syn_values in cmd_info['synonyms'].items():
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
                elif any(word in command.lower() for word in ['down', 'lower', 'decrease', 'quieter', 'softer', 'reduce']):
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
        elif cmd_type == 'open_app':
            app_name = re.sub(r'(?:open|launch|start|run|please|could you|can you)\\s+', '', command).strip()
            if self.system_controller.open_application(app_name):
                responses = [
                    f"Opening {app_name} for you",
                    f"I'll get {app_name} started",
                    f"Sure, launching {app_name} now",
                    f"Right away! Starting {app_name}"
                ]
                self.respond(random.choice(responses))
            else:
                self.respond(f"I couldn't find {app_name}. Could you specify the application name?")
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
        else:
            # For any unrecognized command, try to find relevant information
            self.respond("Let me search for that information")
            result = self.web_search.get_information(command)
            self.respond(result)

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
        if any(word in command for word in ['down', 'lower', 'decrease', 'quieter', 'softer']):
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
        self.is_running = True
        self.listen_thread = threading.Thread(target=self.run_listening)
        self.listen_thread.start()

    def stop_listening(self):
        """Stop the listening process"""
        self.is_running = False
        # Don't wait for the thread to join here
        # Instead, start a new thread to handle the cleanup
        cleanup_thread = threading.Thread(target=self._cleanup_listen_thread)
        cleanup_thread.start()

    def _cleanup_listen_thread(self):
        """Helper method to cleanup the listening thread"""
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)  # Wait for max 1 second
            if self.listen_thread.is_alive():
                print("Warning: Listen thread is taking longer than expected to stop")

    def run_listening(self):
        while self.is_running:
            try:
                detected_speech = self.voice_recognizer.listen_for_command()
                if detected_speech:
                    print(f"\nDetected speech: '{detected_speech}'")
                    self.process_command(detected_speech)
                else:
                    # If speech detection fails, try reinitializing the microphone
                    if not self.voice_recognizer.microphone:
                        print("Attempting to reinitialize microphone...")
                        if self.voice_recognizer.reinitialize_microphone():
                            self.respond("Microphone reinitialized successfully")
                        else:
                            self.respond("Sorry, I'm having trouble with the microphone. Please check your microphone settings.")
                            time.sleep(5)  # Wait before trying again
            except Exception as e:
                print(f"Error in listening loop: {e}")
                self.respond("Sorry, I encountered an error while listening. I'll try to recover.")
                time.sleep(2)  # Brief pause before continuing

    def handle_partial_result(self, text):
        self.on_interim_speech.emit(f"Listening: {text}")

if __name__ == "__main__":
    assistant = VoiceAssistant()
    app, gui = launch_gui(assistant)
    sys.exit(app.exec())

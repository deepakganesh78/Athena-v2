from voice_recognition import VoiceRecognizer
from audio_manager import AudioManager
from system_controller import SystemController
import time
import random
from PyQt6.QtCore import QObject, pyqtSignal
from gui import launch_gui
import threading

class VoiceAssistant(QObject):

	on_speech_detected = pyqtSignal(str)
	on_command_processing = pyqtSignal()
	on_response_ready = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.voice_recognizer = VoiceRecognizer()
		self.audio_manager = AudioManager()
		self.system_controller = SystemController()
		self.is_running = False
		self.listen_thread = None

	def get_available_commands(self):
		commands = [
			"Volume controls:",
			"  - 'volume up' or 'increase volume'",
			"  - 'volume down' or 'decrease volume'",
			"  - 'set volume to [number]'",
			"System controls:",
			"  - 'shutdown'",
			"  - 'restart'",
			"Application control:",
			"  - 'open [application name]'",
			"Information:",
			"  - 'news'",
			"  - 'what's on screen'"
		]
		return commands

	def handle_volume_command(self, command):
		response = ""
		if "set" in command and "to" in command:
			try:
				volume_level = int(''.join(filter(str.isdigit, command)))
				self.audio_manager.set_volume(volume_level)
				responses = [
					f"I've set the volume to {volume_level} percent for you",
					f"Alright, volume is now at {volume_level} percent",
					f"Done! Volume adjusted to {volume_level} percent"
				]
				response = random.choice(responses)
			except:
				response = "I'm having trouble understanding the volume level you want"
		elif "up" in command or "increase" in command:
			self.audio_manager.change_volume(10)
			responses = [
				"I've turned up the volume a bit",
				"Volume's going up",
				"Making it a bit louder for you"
			]
			response = random.choice(responses)
		elif "down" in command or "decrease" in command:
			self.audio_manager.change_volume(-10)
			responses = [
				"I've lowered the volume for you",
				"Volume's going down",
				"Making it a bit quieter"
			]
			response = random.choice(responses)
		self.respond(response)

	def process_command(self, command):
		if not command:
			print("Skipping command processing - no command received")
			return

		command = command.lower()  # Convert to lowercase for easier matching
		print(f"Processing command: '{command}'")
		
		self.on_command_processing.emit()
		self.on_speech_detected.emit(command)

		# Time query
		if any(phrase in command for phrase in ["what's the time", "what time is it", "current time", "tell me the time"]):
			current_time = time.strftime("%I:%M %p")
			self.respond(f"The current time is {current_time}")
			return

		# Greetings
		if any(word in command for word in ["hello", "hi", "hey", "greetings"]):
			responses = [
				"Hello! How can I help you today?",
				"Hi there! What can I do for you?",
				"Hey! I'm here to help!"
			]
			self.respond(random.choice(responses))
			return

		# Name queries
		if "your name" in command:
			responses = [
				"I'm your virtual assistant. You can call me Athena.",
				"My name is Athena, nice to meet you!",
				"I'm Athena, how can I help?"
			]
			self.respond(random.choice(responses))
			return

		# Well-being queries
		if any(phrase in command for phrase in ["how are you", "how're you", "how do you do"]):
			responses = [
				"I'm doing well, thank you! How can I help?",
				"I'm great! What can I do for you?",
				"All systems running smoothly! What do you need?"
			]
			self.respond(random.choice(responses))
			return

		# Weather queries (placeholder response)
		if "weather" in command:
			self.respond("I'm sorry, I don't have access to weather information yet, but I'm working on adding that feature!")
			return

		# Navigation queries (placeholder response)
		if any(phrase in command for phrase in ["route to", "directions to", "how to get to"]):
			destination = command.split("to")[-1].strip()
			self.respond(f"I'm sorry, I don't have navigation capabilities yet, but you're asking about directions to {destination}")
			return

		# Gratitude responses
		if any(phrase in command for phrase in ["thank you", "thanks"]):
			responses = [
				"You're welcome! Let me know if you need anything else.",
				"Glad I could help! What else can I do for you?",
				"Anytime! Feel free to ask for help whenever you need it."
			]
			self.respond(random.choice(responses))
			return

		# Volume controls
		if "volume" in command:
			self.handle_volume_command(command)
			return

		# System controls
		elif "shutdown" in command:
			self.respond("I'll shut down the computer for you now")
			self.system_controller.shutdown_pc()
		elif "restart" in command:
			self.respond("Okay, I'll restart the computer right away")
			self.system_controller.restart_pc()

		# Application controls
		elif "open" in command:
			app_name = command.replace("open", "").strip()
			if self.system_controller.open_application(app_name):
				responses = [
					f"Opening {app_name} for you",
					f"I'll get {app_name} started",
					f"Sure, launching {app_name} now"
				]
				self.respond(random.choice(responses))
			else:
				responses = [
					f"I couldn't find {app_name} on your computer",
					f"I'm having trouble opening {app_name}",
					f"Sorry, but I can't seem to find {app_name}"
				]
				self.respond(random.choice(responses))

		# News
		elif "news" in command:
			self.handle_news_command()

			def handle_news_command(self):
				print("\nAttempting to fetch news headlines...")
				try:
					news_items = self.system_controller.get_latest_news()
					print(f"Debug - Raw news_items: {news_items}")
					
					if news_items is None:
						print("Error: News API returned None")
						self.respond("Sorry, I couldn't fetch the news at the moment")
						return
						
					if not isinstance(news_items, list):
						print(f"Error: Expected list but got {type(news_items)}")
						self.respond("Sorry, there was an error processing the news")
						return
						
					valid_news_items = [str(item) for item in news_items if item is not None and str(item).strip()]
					
					if not valid_news_items:
						print("Error: No valid news items found")
						self.respond("Sorry, no news headlines are available at the moment")
						return
						
					print(f"\nSuccessfully fetched {len(valid_news_items)} headlines")
					print("\nNews Headlines:")
					for idx, item in enumerate(valid_news_items, 1):
						print(f"{idx}. {item}")
					
					responses = [
						"Here's what's making headlines today:",
						"Let me catch you up on the latest news:",
						"Here are the top stories right now:"
					]
					self.respond(random.choice(responses))
					for item in valid_news_items:
						self.respond(item)
						time.sleep(0.5)
						
				except Exception as e:
					print(f"Error in news processing: {str(e)}")
					self.respond("Sorry, there was an error fetching the news")


		# Screen context
		elif "what's on screen" in command or "what is on screen" in command:
			context = self.system_controller.get_screen_context()
			responses = [
				f"You're looking at {context}",
				f"That appears to be {context}",
				f"I can see {context} on your screen"
			]
			self.respond(random.choice(responses))

		else:
			self.handle_unknown_command(command)

	def handle_unknown_command(self, command):
		responses = [
			"I'm not quite sure what you mean by that. Could you rephrase it?",
			"I didn't quite catch that. Could you say it differently?",
			"I'm still learning! Could you try asking in another way?"
		]
		self.respond(random.choice(responses))

	def respond(self, message):
		print(f"Assistant response: {message}")
		self.audio_manager.speak(message)
		self.on_response_ready.emit(message)

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
			except Exception as e:
				print(f"\nError with microphone: {str(e)}")
				error_msg = "Sorry, I'm having trouble with the microphone"
				self.respond(error_msg)
				time.sleep(1)
			time.sleep(0.1)

if __name__ == "__main__":
	assistant = VoiceAssistant()
	launch_gui(assistant)

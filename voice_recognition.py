import speech_recognition as sr
from config import WAKE_WORD
from PyQt6.QtCore import QObject, pyqtSignal

class VoiceRecognizer(QObject):
	on_partial_result = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.recognizer = sr.Recognizer()
		try:
			self.microphone = sr.Microphone()
			with self.microphone as source:
				print("Adjusting for ambient noise...")
				self.recognizer.adjust_for_ambient_noise(source, duration=1)
				print("Microphone initialized successfully")
		except Exception as e:
			print(f"Error initializing microphone: {e}")
			self.microphone = None
		
		# Enable real-time recognition with optimized parameters
		self.recognizer.pause_threshold = 0.5
		self.recognizer.phrase_threshold = 0.3
		self.recognizer.non_speaking_duration = 0.3
		self.recognizer.operation_timeout = 5  # Timeout for API operations

	def listen_for_wake_word(self):
		if not self.microphone:
			print("Error: Microphone not initialized")
			return False

		try:
			with self.microphone as source:
				print("Listening for wake word...")
				audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
			
			try:
				text = self.recognizer.recognize_google(audio).lower()
				return WAKE_WORD in text
			except sr.UnknownValueError:
				return False
			except sr.RequestError as e:
				print(f"Could not request results from speech recognition service: {e}")
				return False
		except Exception as e:
			print(f"Error listening for wake word: {e}")
			return False

	def listen_for_command(self):
		if not self.microphone:
			print("Error: Microphone not initialized")
			return None

		try:
			with self.microphone as source:
				print("\nListening...")
				# Use shorter timeout for more responsive feedback
				audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
				
				# First try to get partial results
				try:
					partial_results = self.recognizer.recognize_google(audio, show_all=True)
					if partial_results and 'alternative' in partial_results:
						for alt in partial_results['alternative']:
							if 'transcript' in alt:
								self.on_partial_result.emit(alt['transcript'].lower())
				except sr.UnknownValueError:
					pass
				except sr.RequestError as e:
					print(f"Error getting partial results: {e}")
				except Exception as e:
					print(f"Unexpected error in partial recognition: {e}")
				
				# Then get final result
				try:
					text = self.recognizer.recognize_google(audio)
					return text.lower()
				except sr.UnknownValueError:
					print("Could not understand audio")
					return None
				except sr.RequestError as e:
					print(f"Could not request results from speech recognition service: {e}")
					return None
				except Exception as e:
					print(f"Unexpected error in speech recognition: {e}")
					return None

		except sr.WaitTimeoutError:
			print("Listening timed out")
			return None
		except Exception as e:
			print(f"Error during listening: {e}")
			return None

	def reinitialize_microphone(self):
		"""Attempt to reinitialize the microphone if it fails"""
		try:
			self.microphone = sr.Microphone()
			with self.microphone as source:
				print("Reinitializing microphone...")
				self.recognizer.adjust_for_ambient_noise(source, duration=1)
				print("Microphone reinitialized successfully")
			return True
		except Exception as e:
			print(f"Error reinitializing microphone: {e}")
			self.microphone = None
			return False
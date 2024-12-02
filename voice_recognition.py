import speech_recognition as sr
from config import WAKE_WORD

class VoiceRecognizer:
	def __init__(self):
		self.recognizer = sr.Recognizer()
		self.microphone = sr.Microphone()
		
		with self.microphone as source:
			self.recognizer.adjust_for_ambient_noise(source)

	def listen_for_wake_word(self):
		with self.microphone as source:
			print("Listening for wake word...")
			audio = self.recognizer.listen(source)
			
		try:
			text = self.recognizer.recognize_google(audio).lower()
			return WAKE_WORD in text
		except:
			return False

	def listen_for_command(self):
		try:
			with self.microphone as source:
				print("\nListening...")
				# Increase timeout to 7 seconds
				audio = self.recognizer.listen(source, timeout=7, phrase_time_limit=7)
				text = self.recognizer.recognize_google(audio)
				return text.lower()
		except sr.WaitTimeoutError:
			return None
		except sr.UnknownValueError:
			return None
		except sr.RequestError:
			print("Could not request results from speech recognition service")
			return None
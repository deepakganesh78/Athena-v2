import pyttsx3
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math
from PyQt6.QtCore import QObject, pyqtSignal
import re

class AudioManager(QObject):
	on_start_speaking = pyqtSignal(str)
	on_word_spoken = pyqtSignal(str)
	on_end_speaking = pyqtSignal()
	on_speaking_started = pyqtSignal()
	on_speaking_finished = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.engine = pyttsx3.init()
		self.setup_voice()
		self.volume_interface = self.get_volume_interface()
		self.current_word = ""
		self.is_speaking = False
		
		# Connect speech engine callbacks
		self.engine.connect('started-word', self.on_word_start)
		self.engine.connect('started-utterance', self._on_speaking_started)
		self.engine.connect('finished-utterance', self._on_speaking_finished)
		self.engine.connect('finished-utterance', self.on_utterance_finished)

	def setup_voice(self):
		voices = self.engine.getProperty('voices')
		# Select female voice
		female_voice = None
		for voice in voices:
			if "female" in voice.name.lower():
				female_voice = voice
				break
		
		if female_voice:
			self.engine.setProperty('voice', female_voice.id)
		else:
			# Fallback to the second voice which is typically female
			self.engine.setProperty('voice', voices[1].id)
		
		# Adjust speech properties for more natural sound
		self.engine.setProperty('rate', 175)  # Slightly faster than default
		self.engine.setProperty('volume', 0.9)  # Slightly lower volume
		self.engine.setProperty('pitch', 1.1)  # Slightly higher pitch for female voice

	def add_speech_markers(self, text):
		"""Format text for better speech synthesis"""
		# Add natural pauses using punctuation
		text = re.sub(r'([.!?])\s*', r'\1 ... ', text)  # Longer pause after sentences
		text = re.sub(r'([,:])\s*', r'\1 ', text)  # Short pause after commas and colons
		
		# Clean up any remaining break markers that might have come from web content
		text = re.sub(r'<break[^>]*>', '', text)
		text = re.sub(r'breaktime\s*=\s*\d+m?s', '', text)
		
		# Remove other SSML-like tags
		text = re.sub(r'<[^>]+>', '', text)
		
		# Clean up multiple spaces and dots
		text = re.sub(r'\s+', ' ', text)
		text = re.sub(r'\.{2,}', '...', text)
		
		return text.strip()

	def preprocess_text(self, text):
		# Convert numbers to words for better pronunciation
		text = re.sub(r'\b(\d+)%\b', r'\1 percent', text)
		text = re.sub(r'\b(\d{1,2}):(\d{2})\b', r'\1 \2', text)  # Better time pronunciation
		
		# Handle abbreviations
		text = re.sub(r'\bDr\.\s', 'Doctor ', text)
		text = re.sub(r'\bMr\.\s', 'Mister ', text)
		text = re.sub(r'\bMrs\.\s', 'Misses ', text)
		text = re.sub(r'\bMs\.\s', 'Miss ', text)
		
		return text

	def speak(self, text):
		"""Speak the given text"""
		if not text:
			return
			
		# Clean and format the text
		formatted_text = self.add_speech_markers(text)
		self.on_start_speaking.emit(formatted_text)
		
		# Split text into words for progressive display
		words = formatted_text.split()
		for word in words:
			self.on_word_spoken.emit(word)
			
		self.engine.say(formatted_text)
		self.engine.runAndWait()
		self.on_end_speaking.emit()

	def on_word_start(self, name, location, length):
		self.current_word = name
		self.on_word_spoken.emit(self.current_word)

	def on_utterance_finished(self, name, completed):
		self.on_end_speaking.emit()

	def _on_speaking_started(self):
		self.is_speaking = True
		self.on_speaking_started.emit()
		
	def _on_speaking_finished(self):
		self.is_speaking = False
		self.on_speaking_finished.emit()

	def get_volume_interface(self):
		devices = AudioUtilities.GetSpeakers()
		interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
		return interface.QueryInterface(IAudioEndpointVolume)

	def set_volume(self, volume_level):
		"""Set system volume to a specific level (0.0 to 1.0)"""
		try:
			if self.volume_interface:
				# Ensure volume is between 0 and 1
				volume_level = max(0.0, min(1.0, volume_level))
				# Convert to decibels for the Windows API
				if volume_level == 0:
					db_volume = -65.25  # Mute
				else:
					db_volume = min(0.0, 20 * math.log10(volume_level))
				self.volume_interface.SetMasterVolumeLevel(db_volume, None)
				return True
		except Exception as e:
			print(f"Error setting volume: {e}")
		return False

	def volume_up(self, step=0.1):
		"""Increase system volume"""
		try:
			if self.volume_interface:
				current_volume = self.volume_interface.GetMasterVolumeLevelScalar()
				new_volume = min(1.0, current_volume + step)
				return self.set_volume(new_volume)
		except Exception as e:
			print(f"Error increasing volume: {e}")
		return False

	def volume_down(self, step=0.1):
		"""Decrease system volume"""
		try:
			if self.volume_interface:
				current_volume = self.volume_interface.GetMasterVolumeLevelScalar()
				new_volume = max(0.0, current_volume - step)
				return self.set_volume(new_volume)
		except Exception as e:
			print(f"Error decreasing volume: {e}")
		return False

	def mute(self):
		"""Mute system volume"""
		try:
			if self.volume_interface:
				self.volume_interface.SetMute(True, None)
				return True
		except Exception as e:
			print(f"Error muting volume: {e}")
		return False

	def unmute(self):
		"""Unmute system volume"""
		try:
			if self.volume_interface:
				self.volume_interface.SetMute(False, None)
				return True
		except Exception as e:
			print(f"Error unmuting volume: {e}")
		return False

	def change_volume(self, change):
		current = self.volume_interface.GetMasterVolumeLevelScalar()
		new_volume = max(0.0, min(1.0, current + (change / 100)))
		self.volume_interface.SetMasterVolumeLevelScalar(new_volume, None)

	def get_audio_devices(self):
		return AudioUtilities.GetAllDevices()

	def switch_audio_device(self, device_name):
		devices = self.get_audio_devices()
		for device in devices:
			if device_name.lower() in device.FriendlyName.lower():
				# Implementation to switch device would go here
				# This requires additional Windows API calls
				return True
		return False
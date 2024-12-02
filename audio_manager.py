import pyttsx3
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import math

class AudioManager:
	def __init__(self):
		self.engine = pyttsx3.init()
		self.setup_voice()
		self.volume_interface = self.get_volume_interface()

	def setup_voice(self):
		voices = self.engine.getProperty('voices')
		self.engine.setProperty('voice', voices[1].id)  # Female voice
		self.engine.setProperty('rate', 150)
		self.engine.setProperty('volume', 1.0)

	def get_volume_interface(self):
		devices = AudioUtilities.GetSpeakers()
		interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
		return interface.QueryInterface(IAudioEndpointVolume)

	def speak(self, text):
		self.engine.say(text)
		self.engine.runAndWait()

	def set_volume(self, volume_percent):
		volume = volume_percent / 100
		self.volume_interface.SetMasterVolumeLevelScalar(volume, None)

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
import os
import subprocess
import psutil
import pyautogui
from newsapi import NewsApiClient
from config import NEWS_API_KEY

class SystemController:
	def __init__(self):
		self.newsapi = NewsApiClient(api_key=NEWS_API_KEY)

	def open_application(self, app_name):
		app_paths = {
			"word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
			"excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
			# Add more applications as needed
		}
		
		try:
			if app_name.lower() in app_paths:
				subprocess.Popen(app_paths[app_name.lower()])
			else:
				os.system(f"start {app_name}")
			return True
		except Exception as e:
			print(f"Error opening application: {e}")
			return False

	def shutdown_pc(self):
		os.system("shutdown /s /t 1")

	def restart_pc(self):
		os.system("shutdown /r /t 1")

	def sleep_pc(self):
		"""Put the computer into sleep mode"""
		try:
			os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
			return True
		except Exception as e:
			print(f"Error putting computer to sleep: {e}")
			return False

	def get_screen_context(self):
		# Capture the active window title
		window_title = pyautogui.getActiveWindow().title
		return window_title

	def get_latest_news(self, category='general'):
		try:
			news = self.newsapi.get_top_headlines(category=category, language='en', country='us')
			return [article['title'] for article in news['articles'][:5]]
		except Exception as e:
			return [f"Error fetching news: {str(e)}"]
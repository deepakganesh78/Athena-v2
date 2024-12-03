import os
import subprocess
import psutil
import pyautogui
from newsapi import NewsApiClient
from config import NEWS_API_KEY
import winreg
import glob

class SystemController:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        self.app_paths = self._get_installed_apps()

    def _get_installed_apps(self):
        """Get dictionary of installed applications and their paths"""
        apps = {}
        
        # Common paths for applications
        program_paths = [
            os.environ.get('ProgramFiles', ''),
            os.environ.get('ProgramFiles(x86)', ''),
            os.environ.get('LocalAppData', ''),
            os.path.join(os.environ.get('LocalAppData', ''), 'Programs'),
            os.path.join(os.environ.get('AppData', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        ]
        
        # Common browsers
        browsers = {
            'chrome': ['Google', 'Chrome', 'Application', 'chrome.exe'],
            'firefox': ['Mozilla Firefox', 'firefox.exe'],
            'edge': ['Microsoft', 'Edge', 'Application', 'msedge.exe'],
            'brave': ['BraveSoftware', 'Brave-Browser', 'Application', 'brave.exe']
        }
        
        # Add browsers
        for browser, path_parts in browsers.items():
            for program_path in program_paths:
                potential_path = os.path.join(program_path, *path_parts)
                if os.path.exists(potential_path):
                    apps[browser] = potential_path
                    break
        
        # Add Microsoft Office applications
        office_path = r"C:\Program Files\Microsoft Office\root\Office16"
        if os.path.exists(office_path):
            apps.update({
                'word': os.path.join(office_path, 'WINWORD.EXE'),
                'excel': os.path.join(office_path, 'EXCEL.EXE'),
                'powerpoint': os.path.join(office_path, 'POWERPNT.EXE'),
                'outlook': os.path.join(office_path, 'OUTLOOK.EXE')
            })
        
        # Add Windows built-in apps
        windows_apps = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'paint': 'mspaint.exe',
            'cmd': 'cmd.exe',
            'explorer': 'explorer.exe',
            'settings': 'ms-settings:',
            'control': 'control.exe'
        }
        apps.update(windows_apps)
        
        return apps

    def open_application(self, app_name):
        """Open an application by name"""
        app_name = app_name.lower().strip()
        
        try:
            # Check if it's in our known apps
            if app_name in self.app_paths:
                path = self.app_paths[app_name]
                if path.startswith('ms-'):  # Windows Settings
                    os.system(f'start {path}')
                else:
                    subprocess.Popen(path)
                return f"Opening {app_name}"
            
            # Try to launch directly if it's an executable name
            if app_name.endswith('.exe'):
                os.system(f'start {app_name}')
                return f"Attempting to open {app_name}"
            
            # Try Windows Run command as last resort
            os.system(f'start {app_name}')
            return f"Attempting to open {app_name}"
            
        except Exception as e:
            print(f"Error opening application: {e}")
            return f"Sorry, I couldn't open {app_name}"

    def close_application(self, app_name):
        """Close an application by name"""
        app_name = app_name.lower().strip()
        
        try:
            # Get all running processes
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    # Check process name
                    proc_name = proc.info['name'].lower()
                    if app_name in proc_name or app_name + '.exe' == proc_name:
                        proc.terminate()
                        return f"Closing {app_name}"
                    
                    # Check executable path
                    if proc.info['exe']:
                        exe_name = os.path.basename(proc.info['exe']).lower()
                        if app_name in exe_name or app_name + '.exe' == exe_name:
                            proc.terminate()
                            return f"Closing {app_name}"
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return f"Couldn't find {app_name} running"
            
        except Exception as e:
            print(f"Error closing application: {e}")
            return f"Sorry, I couldn't close {app_name}"

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
import subprocess
import sys
import time

def pip_install(package):
	try:
		print(f"Installing {package}...")
		subprocess.check_call([sys.executable, "-m", "pip", "install", package])
		return True
	except subprocess.CalledProcessError:
		print(f"Failed to install {package}")
		return False

def install_dependencies():
	print("Starting dependency installation...")
	
	# Check Python version
	python_version = sys.version_info
	if python_version.major == 3 and python_version.minor >= 13:
		print("WARNING: This application requires Python 3.11 or lower due to dependency requirements.")
		print("Current Python version:", sys.version)
		print("Please install Python 3.11 and run this script again.")
		input("Press Enter to exit...")
		sys.exit(1)
	
	# First, upgrade pip
	print("Upgrading pip...")
	subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
	
	# Install setuptools first
	print("Installing setuptools...")
	pip_install("setuptools")
	
	# Try to install aifc separately (might be needed for Python 3.12+)
	try:
		print("Installing aifc...")
		pip_install("aifc")
	except:
		print("Note: aifc installation failed, but this might be okay if using Python 3.11 or lower")
	
	# Install critical packages first
	critical_packages = [
		"SpeechRecognition",
		"PyAudio"
	]
	
	for package in critical_packages:
		if not pip_install(package):
			if package == "PyAudio":
				print("\nPyAudio installation failed. You might need to install it manually.")
				print("For Windows, download the appropriate .whl file from:")
				print("https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
				print("Then install it using: pip install <downloaded_file_name>.whl")
			else:
				print(f"\nCritical package {package} installation failed.")
			input("Press Enter to continue with other dependencies...")

	# Install remaining requirements
	print("\nInstalling remaining dependencies from requirements.txt...")
	try:
		subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
	except subprocess.CalledProcessError:
		print("Some packages from requirements.txt failed to install.")
	
	print("\nInstallation process completed!")
	print("\nInstalled packages:")
	subprocess.check_call([sys.executable, "-m", "pip", "list"])
	
	print("\nPress Enter to exit...")
	input()

if __name__ == "__main__":
	try:
		install_dependencies()
	except Exception as e:
		print(f"An error occurred: {str(e)}")
		print("\nPress Enter to exit...")
		input()
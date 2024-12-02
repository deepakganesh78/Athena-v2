# Voice Assistant

A modern voice assistant with GUI interface that can control your system, manage volume, fetch news, and more.

## Features

- System controls (shutdown, restart)
- Volume controls (increase, decrease, set specific level)
- Application launching
- News headlines fetching
- Screen context awareness
- Modern GUI interface with start/stop listening button

## Installation

1. Make sure you have Python 3.8 or higher installed
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Required Dependencies

- PyQt6 (GUI interface)
- speech_recognition (voice recognition)
- pyttsx3 (text-to-speech)
- requests (for news API)
- pycaw (volume control)

## Usage

1. Launch the application using `python main.py`
2. Click the "Start Listening" button to begin voice recognition
3. Speak commands clearly into your microphone
4. Click "Stop Listening" when you're done

## Available Commands

- "Set volume to [number]" - Sets system volume to specified percentage
- "Volume up" or "Increase volume" - Increases volume by 10%
- "Volume down" or "Decrease volume" - Decreases volume by 10%
- "Shutdown" - Initiates system shutdown
- "Restart" - Initiates system restart
- "Open [application]" - Launches specified application
- "Get news" - Fetches and reads latest news headlines
- "What's on screen" - Describes current screen context
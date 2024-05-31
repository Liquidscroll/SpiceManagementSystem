import io
import sys
import numpy as np
import soundfile as sf
import speech_recognition as sr
import threading
from functools import partial

# This is used to supress ASLA errors.
import sounddevice

import firebase_admin
from firebase_admin import credentials, db

from faster_whisper import WhisperModel

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QLabel, QDialog,
    QLineEdit, QMessageBox, QDialogButtonBox, QDesktopWidget
)

# Initialize Firebase
cred = credentials.Certificate("./db_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'YOUR_DB_LINK_HERE'
})


class SpiceButton(QPushButton):
    def __init__(self, index, spice="Empty"):
        super().__init__()
        self.spice = spice
        self.index = index
        self.setText(f'POS {index}: {spice}')

        # Initialize a timer for detecting long presses
        self.longPressTimer = QTimer(self)
        self.longPressTimer.setSingleShot(True)
        self.longPressTimer.timeout.connect(self.OnLongPress)
        self.longPressThreshold = 1000
        self.isLongPress = False

        self.pressed.connect(self.StartLongPressTimer)
        self.released.connect(self.CheckLongPress)

    def SetSpice(self, newSpice):
        self.spice = newSpice
        self.setText(f'POS {self.index}: {self.spice}')

    def StartLongPressTimer(self):
        self.isLongPress = False
        self.longPressTimer.start(self.longPressThreshold)

    def OnLongPress(self):
        self.isLongPress = True
        self.OpenModificationWindow()

    def CheckLongPress(self):
        if self.longPressTimer.isActive():
            self.longPressTimer.stop()
            self.SendMovementCommand()

    def OpenModificationWindow(self):
        self.parent().parent().OpenEditDialog(self)

    def SendMovementCommand(self):
        self.parent().parent().UpdatePosition(self.index)


class EditDialog(QDialog):
    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.button = button
        self.InitUI()

    def InitUI(self):
        self.setWindowTitle('Edit Spice')

        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), 100)

        self.mainLayout = QVBoxLayout()

        self.input = QLineEdit(self)
        self.input.setPlaceholderText('Enter New Spice Name')

        self.mainLayout.addWidget(self.input)

        self.clearButton = QPushButton('Clear Spice Position', self)
        self.clearButton.clicked.connect(self.ClearPosition)
        self.mainLayout.addWidget(self.clearButton)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.RenamePosition)
        self.buttons.rejected.connect(self.reject)

        self.mainLayout.addWidget(self.buttons)

        self.setLayout(self.mainLayout)

    def RenamePosition(self):
        newName = self.input.text().strip()
        if newName:
            self.button.SetSpice(newName)
            self.parent.spiceDict[self.button.index] = newName
        self.accept()

    def ClearPosition(self):
        self.button.SetSpice("Empty")
        self.accept()


class VerticalButtonGroup(QWidget):
    def __init__(self, startIndex, spiceData):
        super().__init__()
        self.InitUI(startIndex, spiceData)

    def InitUI(self, startIndex, spiceData):
        mainLayout = QVBoxLayout()

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        self.buttons = []
        for i in range(0, 4):
            btn_idx = startIndex + i + 1
            button = myButton(btn_idx, spiceData[btn_idx])
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            mainLayout.addWidget(button, 1)
            self.buttons.append(button)

        self.setLayout(mainLayout)


class WhisperSpeechSystem(QObject):
    listeningFinished = pyqtSignal()

    def __init__(self, model, computeType, mainWindow):
        super().__init__()

        self.mainWindow = mainWindow
        self.model = WhisperModel(model, device="cpu", compute_type=computeType)
        self.recogniser = sr.Recognizer()
        self.microphone = sr.Microphone

    def HandleText(self, inputString):
        words = [word.lower().strip().rstrip('.') for word in inputString.split()]
        for word in words:
            for index, spice in self.mainWindow.spiceDict.items():
                print(f"Got word: {word}  , spice: {spice.lower()}")
                if word == spice.lower():
                    self.mainWindow.UpdatePosition(index)
                    return

    def Listen(self):
        with self.microphone() as source:
            audio = self.recogniser.listen(source)

        try:
            self.FasterRecognise(audio)
        finally:
            self.listeningFinished.emit()

    def FasterRecognise(self, audioData):
        wavBytes = audioData.get_wav_data(convert_rate=16000)
        wavStream = io.BytesIO(wavBytes)
        audioArray, _ = sf.read(wavStream, dtype='float32')
        audioArray = audioArray.astype(np.float32)

        segments, _ = self.model.transcribe(audioArray, beam_size=3, vad_filter=True)
        for segment in segments:
            self.HandleText(segment.text)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.spiceDict = {}
        self.currPos = None
        self.LoadDB()
        self.InitUI()
        self.UpdatePosition(self.currPos)
        self.voiceSystem = WhisperSpeechSystem(model="tiny.en", computeType="int8", mainWindow=self)
        self.voiceSystem.listeningFinished.connect(self.OnListeningFinished)
        self.listening = False

    def StartVoiceRecognition(self):
        if not self.listening:
            self.listening = True
            self.voiceButton.setText('Listening...')
            self.voiceButton.setStyleSheet("QPushButton {background-color: #b1b9e3; border: none}")
            threading.Thread(target=self.voiceSystem.Listen).start()

    def OnListeningFinished(self):
        self.listening = False
        self.voiceButton.setStyleSheet("")
        self.voiceButton.setStyleSheet('Start Listening')

    def OnExitButtonClick(self):
        self.close()

    def InitUI(self):
        mainLayout = QVBoxLayout()

        diagLayout = QHBoxLayout()

        diagLayout.addWidget(QLabel('Long Press to Modify Position'))

        self.voiceButton = QPushButton('Start Listening...')
        self.voiceButton.clicked.connect(self.StartVoiceRecognition)
        diagLayout.addWidget(self.voiceButton)

        exitButton = QPushButton('Exit')
        exitButton.clicked.connect(self.OnExitButtonClick)
        diagLayout.addWidget(exitButton)

        mainLayout.addLayout(diagLayout)

        buttonLayout = QHBoxLayout()

        buttonLayout.setSpacing(0)
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        for i in [0, 4, 8]:
            column = VerticalButtonGroup(i, self.spiceDict)
            buttonLayout.addWidget(column)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.setWindowTitle('Spice Management')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

    def LoadDB(self):
        ref = db.reference('')
        children = ref.get()
        if children:
            for key, value in children.items():
                if key == 'position':
                    self.currPos = value
                    continue
                self.spiceDict[int(key)] = value

    def UpdatePosition(self, index):
        if self.currPos is not None:
            self.SetButtonColour(self.currPos, "")
        self.currPos = index
        self.SetButtonColour(index, "QPushButton {background-color: #c4e3c3; border: none}")

        ref = db.reference('')
        ref.child('position').set(index)

    def SetButtonColour(self, index, color):
        for button in self.findChildren(myButton):
            if button.index == index:
                button.setStyleSheet(color)

    def UpdateDBFromButton(self, button):
        ref = db.reference('')
        ref.child(str(button.index)).set(button.spice)

    def OpenEditDialog(self, button):
        dialog = EditDialog(button, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.UpdateDBFromButton(button)


if __name__ == '__main__':
    app = QApplication([])
    wind = MainWindow()
    try:
        app.exec_()
    except KeyboardInterrupt:
        exit()

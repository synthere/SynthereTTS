import os
import sys
import struct
import threading

from mainsyn import Ui_MainWindow

from PyQt5.QtCore import QSize, Qt, QUrl, pyqtSignal, QTimer, QBuffer, QByteArray
from PyQt5.QtGui import QColor, QPalette, QIcon, QPixmap
from PyQt5.QtMultimedia import (
    QMediaPlayer,
    QAudioFormat, QAudioOutput, QAudio
)
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

import basictts
import gpttts

import soundfile as sf

class ViewerWindow(QMainWindow):
    state = pyqtSignal(bool)

    def closeEvent(self, e):
        # Emit the window state, to update the viewer toggle button.
        self.state.emit(False)


def get_base_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return base_path

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.audioDuration = 0
        self.cur_play_time = "0:00"
        self.basicTTS = basictts.BasicTTS()
        self.basic_model = 'amy'
        self.audio_data = []
        self.audio_sr = 0
        self.user_play = False  #
        self.is_playing = False  # real play stat
        self.current_audio_index = 0
        self.sample_size = 16
        self.audio_output = None
        self.buffer = None
        self.is_slider_pressed = False
        self.slid_previous_value = 0
        self.text = "Input your text here"
        self.wordcnt.setText(str(len(self.text)) + '/500')
        self.slide_pos_offset = 0
        self.max_duration_ms = 0
        self.emphasize = 0
        self.denoise = 0
        self.ref_audio_file = ''
        self.saved_file = ''

        self.emph_check.stateChanged.connect(self.empha_check_changed)
        self.denoise_check.stateChanged.connect(self.denoise_check_changed)

        # Add viewer for video playback, separate floating window.
        self.viewer = ViewerWindow(self)
        self.viewer.setWindowFlags(
            self.viewer.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        self.viewer.setMinimumSize(QSize(480, 360))
        self.plainTextEdit.textChanged.connect(self.countWords)

        self.playBut.pressed.connect(self.toggle_play)
        self.selectaudio.pressed.connect(self.select_audio_file)

        self.synthbut.clicked.connect(self.synth)

        self.horizontalSlider.sliderMoved.connect(self.slider_moved)
        self.horizontalSlider.sliderPressed.connect(self.slider_pressed)
        self.horizontalSlider.sliderReleased.connect(self.slider_released)
        self.horizontalSlider.valueChanged.connect(self.slider_moved)
        self.base_path = get_base_path()
        self.playBut.setIcon(self.get_icon(self.get_abspath('./resource/play.svg')))
        self.downbut.setIcon(self.get_icon(self.get_abspath('./resource/download.svg')))
        self.downbut.pressed.connect(self.save_audio_file)

        self.chinese_count = 0
        self.audio_bytes = []

        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

        self.show()
    def get_abspath(self, relpath):
        return os.path.join(self.base_path, relpath)
    def show_about_dialog(self):
        about_text = "<h3>Synthere TTS 1.1</h3>" \
                     "<p style='font-size: 12px;'>Copyright © 2024 <a href='https://www.synthere.net'>Synthere</a></p>"
                     #"<ul style='font-size: 14px;'>" \
                     #"<li>More info <a href='https://www.example.com'>Synthere</a></li>" \
                     #"</ul>"

        about_box = QMessageBox()
        about_box.setWindowTitle("About")
        about_box.setTextFormat(1)
        about_box.setText(about_text)

        #pixmap = QPixmap("image.png")
        #about_box.setIconPixmap(pixmap)

        about_box.exec()

    def empha_check_changed(self, state):
        if 2 == state:
            self.emphasize = 1
        else:
            self.emphasize = 0

    def denoise_check_changed(self, state):
        if 2 == state:
            self.denoise = 1
        else:
            self.denoise = 0

    def select_audio_file(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, 'Select audio file', '', 'Audio File(*.wav *.mp3 *.flac);;All Files (*)',
                                              options=options)
        self.ref_audio_file = file
        self.refaudio.setText(': ' + os.path.basename(file))

    @staticmethod
    def validate_audio_filename(filename):
        name, ext = os.path.splitext(filename)
        if ext.lower() == ".mp3" or ext.lower() == ".wav":
            print("valid ex")
        else:
            filename = name + ".wav"

        if filename.endswith(('.wav', '.mp3')):
            print("valid filname")
        else:
            filename = filename + ".wav"
        return filename

    def save_audio_file(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        file, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'Audio File(*.wav *.mp3);;All Files (*)',
                                              options=options)
        print("set file:", file)
        if "" == file.strip():
            return
        file = self.validate_audio_filename(file)
        print("save to", file)

        if self.audio_duration_sec > 0 and len(self.audio_data) > 0:
            self.statusBar().showMessage("save to to:" + file)
            print("saved to", file, self.audio_sr)
            sf.write(file, self.audio_data, self.audio_sr, 'PCM_16')
            self.statusBar().clearMessage()
        self.saved_file = file

    @staticmethod
    def format_time(seconds):
        minutes = seconds // 60
        second = seconds % 60
        return f"{minutes}:{second:02d}"

    def get_icon(self, relative_path):
        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(self.base_path, relative_path)), QIcon.Normal, QIcon.Off)
        return icon

    def toggle_play(self):
        if not self.is_playing:
            self.user_play = True
            self.is_playing = True
            self.playBut.setIcon(self.get_icon(self.get_abspath('./resource/pause.svg')))
            self.play()
        else:
            self.user_play = False
            self.pause()

    def pause(self):
        self.is_playing = False
        self.playBut.setIcon(self.get_icon(self.get_abspath('./resource/play.svg')))
        self.audio_output.suspend()
        self.timer.stop()

    def resume(self):
        self.is_playing = True
        self.playBut.setIcon(self.get_icon(self.get_abspath('./resource/pause.svg')))
        self.play()

    def finish(self):
        self.is_playing = False
        self.playBut.setIcon(self.get_icon(self.get_abspath('./resource/play.svg')))
        self.timer.stop()
        self.audio_output.reset()
        print("finish set")
        self.user_play = False  # force stop
        self.slid_previous_value = 0

        # self.set_position(self.slid_previous_value)
        self.horizontalSlider.setSliderPosition(self.slid_previous_value)
        self.audiolen.setText("0:00" + '/' + self.format_time(self.audio_duration_sec))

    def play(self):
        if 0 >= len(self.audio_data):
            print("play overr")
            return
        if self.audio_output != None:
            print("outputstat:", self.audio_output.state(), QAudio.State.StoppedState)

        if self.audio_output is None or self.audio_output.state() == QAudio.State.StoppedState:
            self.buffer = QBuffer()
            self.buffer.setData(QByteArray(self.audio_bytes))
            self.buffer.open(QBuffer.ReadOnly)
            print("audio bytes size:", len(self.audio_bytes), self.buffer.size())
            audio_format = QAudioFormat()
            audio_format.setSampleRate(self.audio_sr)
            audio_format.setChannelCount(1)
            audio_format.setSampleSize(self.sample_size)
            audio_format.setCodec("audio/pcm")
            audio_format.setByteOrder(QAudioFormat.LittleEndian)
            audio_format.setSampleType(QAudioFormat.SignedInt)

            self.audio_output = QAudioOutput(audio_format)
        if self.slid_previous_value >= self.max_duration_ms:
            self.slid_previous_value = 0

        print("to setposi")
        self.set_position(self.slid_previous_value)
        print("to play start:", self.slid_previous_value, "buf size:", self.buffer.size())
        self.audio_output.start(self.buffer)
        self.max_duration_ms = self.buffer.size() // (self.sample_size // 8) // (self.audio_sr // 1000)
        self.horizontalSlider.setMaximum(self.max_duration_ms)
        print("maxx:", self.max_duration_ms)
        self.update_position()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(200)

    def update_position(self):
        if self.is_slider_pressed:
            return
        self.duration_ms = self.slide_pos_offset + self.audio_output.processedUSecs() // 1000
        self.horizontalSlider.setValue(self.duration_ms)
        position_str = self.format_playtime(self.duration_ms)
        self.audiolen.setText(position_str + '/' + self.format_time(self.audio_duration_sec))

        if (self.duration_ms + 50) >= self.max_duration_ms:
            self.finish()

    def set_position(self, position):
        position_bytes = position * (self.audio_sr // 1000) * (self.sample_size // 8)
        print("position:", position, "max:", self.audio_duration_sec, "posbytes:", position_bytes, "totalbyte:",
              len(self.audio_data))
        self.buffer.seek(position_bytes)
        self.slide_pos_offset = position

    def slider_pressed(self):
        self.is_slider_pressed = True
        self.pause()

    def slider_released(self):
        self.is_slider_pressed = False
        print("slide released to set val:", self.slid_previous_value, self.user_play)
        self.horizontalSlider.setSliderPosition(self.slid_previous_value)
        self.set_position(self.slid_previous_value)
        if self.user_play:
            print("to resume")
            self.resume()

    def slider_moved(self, value):
        print("Slider moved:", value)
        self.slid_previous_value = value

    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.current_audio_index += 1
            self.play_audio()

    def format_playtime(self, position):
        minutes = int(position / 60000)
        seconds = int((position % 60000) / 1000)
        return "{:01d}:{:02d}".format(minutes, seconds)

    def synth(self):
        self.synthbut.setText("Terminate")
        self.synthbut.setEnabled(False)

        # Introduce a small delay before executing the task
        #QTimer.singleShot(100, self.synthTask)

        print("to create")
        thread = threading.Thread(target=self.synthTask)
        print("to start")
        thread.start()
        #QTimer.singleShot(100, )
        print("to wait finish")
        #thread.join()

        #task = asyncio.create_task(self.synthTask)

    def synth_function(self, queue):
        result = self.synthTask()
        queue.put(result)

    def synthTask(self):
        self.audiolen.setText("0:00/0:00")
        self.synthbut.setText("Terminate")
        if 0 == self.tabWidget.currentIndex():
            self.basic_model = self.modbasic.currentText()
            print("mod select:", self.basic_model)
            if not self.validate_text(self.basic_model):
                print("unmatched model and text")
                self.synthbut.setText("Generate")
                self.synthbut.setEnabled(True)
                return
            self.audio_data, dur, self.audio_sr = self.basicTTS.generate(self.text, self.basic_model)

            self.audio_duration_sec = int(dur)
            print("duration:", self.audio_duration_sec)
            QApplication.processEvents()
            self.synthbut.setText("Generate")
            self.synthbut.setEnabled(True)
            self.slid_previous_value = 0
            self.horizontalSlider.setSliderPosition(self.slid_previous_value)
            self.audiolen.setText("0:00" + '/' + self.format_time(self.audio_duration_sec))
            audio_data_int = [int(sample * 32767) for sample in self.audio_data]
            self.audio_bytes = struct.pack('h' * len(self.audio_data), *audio_data_int)
        else:
            print("to start generate")
            if '' == self.ref_audio_file:
                self.statusBar().showMessage("Please set audio file first")
                self.synthbut.setText("Generate")
                self.synthbut.setEnabled(True)
                return
            else:
                self.statusBar().clearMessage()

            self.audio_sr,  self.audio_data = gpttts.generate_tts(self.text, self.ref_audio_file, self.emphasize, self.denoise)

            self.audio_duration_sec = int(len(self.audio_data) / self.audio_sr)
            print("duration:", self.audio_duration_sec)
            QApplication.processEvents()
            self.synthbut.setText("Generate")
            self.synthbut.setEnabled(True)
            self.audiolen.setText("0:00" + '/' + self.format_time(self.audio_duration_sec))
            self.audio_bytes = struct.pack('h' * len(self.audio_data), *self.audio_data)

    def validate_text(self, model):
        if model == 'Amy-en' or model == 'Danny-en':
            if self.chinese_count > 0:
                return False
        return True
    def countWords(self):
        self.text = self.plainTextEdit.toPlainText()
        self.chinese_count = len([char for char in self.text if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF])

        totalcnt = len(self.text)
        self.wordcnt.setText(str(totalcnt) + '/500')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Synthere")
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)
    app.setStyleSheet(
        "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
    )

    app.setWindowIcon(QIcon(os.path.join(get_base_path(), "./resource/app.png")))
    window = MainWindow()
    app.exec_()

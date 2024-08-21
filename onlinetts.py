#!/usr/bin/env python3

import argparse
import time

import soundfile as sf
import edge_tts
import asyncio
import re
import sys
import time
import  librosa

class OnlineTTS:
    def __init__(self):
        self.text = ''
        self.output_filename = './' + 'result' + '.wav'
    def get_voice(self,text=None, role=None, rate="+0%", filename=None, pitch="+0Hz", volume="+0%"):
        if not re.match(r'^[+-]\d+%$', volume):
            volume = '+0%'
        if not re.match(r'^[+-]\d+%$', rate):
            rate = '+0%'
        if not re.match(r'^[+-]\d+Hz$', pitch, re.I):
            pitch = '+0Hz'
        communicate = edge_tts.Communicate(text, role, rate=rate, volume=volume, pitch=pitch)
        try:
            asyncio.run(communicate.save(filename))
        except Exception as e:
            err = str(e)
            if err.find("Invalid response status") > 0 or err.find('WinError 10054') > -1:
                time.sleep(10)
                return self.get_voice(
                    text=text,
                    role=role,
                    rate=rate,
                    filename=filename,
                    pitch=pitch,
                    volume=volume
                )
            raise
        else:
            return True
    def generate(self, text, role):
        em_char = '[]()'
        for cha in em_char:
            text = text.replace(cha, '')
        self.text = text
        print("to generate:", text)
        self.get_voice(text=self.text, role=role, rate="+0%", pitch="+2Hz", filename=self.output_filename)
        audio, rate = librosa.load(self.output_filename, sr=16000)

        if len(audio) == 0:
            print("Error in generating audios. Please read previous error messages.")
            return
        audio_duration = len(audio) / rate

        print(f"Saved to {self.output_filename}")
        print(f"The text is '{self.text}'")

        print(f"Audio duration in seconds: {audio_duration:.3f}")

        return audio, audio_duration, rate


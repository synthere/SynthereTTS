#!/usr/bin/env python3

import argparse
import time

import sherpa_onnx
import soundfile as sf
import os, sys

class BasicTTS:
    def __init__(self):
        self.text = ''
        self.vits_model = ''
        self.vits_lexicon = ''
        self.vits_data_dir = ''
        self.vits_tokens = ''
        self.provider = 'cpu'
        self.debug = False
        self.num_threads = 1
        self.tts_rule_fsts = ''
        self.max_num_sentences = 2
        self.sid = 0
        self.speed = 1.0
        self.output_filename = './'+ 'result' + '.wav'
        self.base_path = self.get_base_path()
    def get_base_path(self):
        if getattr(sys, 'frozen', False):  # 是否Bundle Resource
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return base_path

    def resource_path(self, relative_path):
        return os.path.join(self.base_path, relative_path)

    def getconfig(self, model):

        print("base path:", self.base_path)
        if 'Amy-en' == model:
            self.vits_model = self.resource_path("./vctk/vits-vctk.onnx")
            self.vits_lexicon = self.resource_path("./vctk/lexicon.txt")
            self.vits_tokens = self.resource_path("./vctk/tokens.txt")
            self.sid = 66
        elif 'Danny-en' == model:
            self.vits_model = self.resource_path("./vctk/vits-vctk.onnx")
            self.vits_lexicon = self.resource_path("./vctk/lexicon.txt")
            self.vits_tokens = self.resource_path("./vctk/tokens.txt")
            self.sid = 30
        elif 'Ray-zh' == model:
            self.vits_model = self.resource_path("./eula/eula.onnx")
            self.vits_lexicon = self.resource_path("./eula/lexicon.txt")
            self.vits_tokens = self.resource_path("./eula/tokens.txt")
            self.sid = 666
        elif 'John-zh' == model:
            self.vits_model = self.resource_path("./aishell3/vits-aishell3.onnx")
            self.vits_lexicon = self.resource_path("./aishell3/lexicon.txt")
            self.vits_tokens = self.resource_path("./aishell3/tokens.txt")
            self.tts_rule_fsts = self.resource_path("./aishell3/rule.fst")
            self.sid = 21
        elif 'May-zh' == model:
            self.vits_model = self.resource_path("./eula/eula.onnx")
            self.vits_lexicon = self.resource_path("./eula/lexicon.txt")
            self.vits_tokens = self.resource_path("./eula/tokens.txt")
            self.tts_rule_fsts = self.resource_path("./eula/rule.fst")
            self.sid = 99
        elif 'Lily-zh' == model:
            self.vits_model = self.resource_path("./aishell3/vits-aishell3.onnx")
            self.vits_lexicon = self.resource_path("./aishell3/lexicon.txt")
            self.vits_tokens = self.resource_path("./aishell3/tokens.txt")
            self.tts_rule_fsts = self.resource_path("./aishell3/rule.fst")
            self.sid = 99#66
    def get_chinese_cnt(self, text):
        return len([char for char in text if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF])

    def generate(self, text, model):
        self.getconfig(model)
        self.text = text
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=self.vits_model,
                    lexicon=self.vits_lexicon,
                    data_dir=self.vits_data_dir,
                    tokens=self.vits_tokens,
                ),
                provider=self.provider,
                debug=self.debug,
                num_threads=self.num_threads,
            ),
            rule_fsts=self.tts_rule_fsts,
            max_num_sentences=self.max_num_sentences,
        )
        if not tts_config.validate():
            raise ValueError("Please check your config")

        tts = sherpa_onnx.OfflineTts(tts_config)

        start = time.time()
        audio = tts.generate(self.text, sid=self.sid, speed=self.speed)
        end = time.time()

        if len(audio.samples) == 0:
            print("Error in generating audios. Please read previous error messages.")
            return

        elapsed_seconds = end - start
        audio_duration = len(audio.samples) / audio.sample_rate
        real_time_factor = elapsed_seconds / audio_duration

        sf.write(
            self.output_filename,
            audio.samples,
            samplerate=audio.sample_rate,
            subtype="PCM_16",
        )
        print(f"Saved to {self.output_filename}")
        print(f"The text is '{self.text}'")
        print(f"Elapsed seconds: {elapsed_seconds:.3f}")
        print(f"Audio duration in seconds: {audio_duration:.3f}")
        print(f"RTF: {elapsed_seconds:.3f}/{audio_duration:.3f} = {real_time_factor:.3f}")

        return audio.samples, audio_duration, audio.sample_rate


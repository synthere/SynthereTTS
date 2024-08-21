import ffmpeg
import numpy as np
import copy
import librosa
import soundfile as sf

def load_audio(file, sr):
    try:
        # https://github.com/openai/whisper/blob/main/whisper/audio.py#L26
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
        file = (
            file.strip(" ").strip('"').strip("\n").strip('"').strip(" ")
        )  # 防止小白拷路径头尾带了空格和"和回车
        out, _ = (
            ffmpeg.input(file, threads=0)
            .output("-", format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load audio: {e}")

    return np.frombuffer(out, np.float32).flatten()

def denoise_wav(y):
    print("type denos:", type(y))
    y = np.array(y)
    print("type shape y:", y.shape)
    stft_data = librosa.stft(y)
    magnitude = np.abs(stft_data)
    phase = np.angle(stft_data)
    noise_magnitude = np.median(magnitude, axis=1)
    noise_gain = 1.0
    subtraction_constant = 0.01
    processed_magnitude = np.maximum(magnitude - noise_gain * noise_magnitude[:, np.newaxis] - subtraction_constant,
                                     0.0)
    processed_stft = processed_magnitude * np.exp(1j * phase)
    processed_audio = librosa.istft(processed_stft)
    return processed_audio
def change_dynamic(audio, sample_rate):
    audio_normalized = audio / np.max(np.abs(audio))

    threshold = 0.1
    compression_ratio = 0.5

    window_size = int(sample_rate * 0.01)
    audio_squared = audio_normalized ** 2
    energy = np.sqrt(np.convolve(audio_squared, np.ones(window_size) / window_size, mode='same'))

    gain = np.ones_like(audio_normalized)
    for i in range(len(gain)):
        if energy[i] > threshold:
            gain[i] = 1 - compression_ratio * (energy[i] - threshold) / (1 - threshold)
        #gain[i] = gain[i] * (len(gain) - i/80) / i

    audio_compressed = audio_normalized * gain
    rescale = 1
    if max(audio_compressed)/np.max(np.abs(audio)) > 1.1:
        rescale = np.max(np.abs(audio)) * 1.1 / max(audio_compressed)
    audio_compressed *= rescale
    return audio_compressed
def change_speed_rosa(audio, sr, playback_speed):
    if len(audio.shape) > 1:
        print("audioshape:", audio.shape)
        audio = np.mean(audio, axis=1)

    target_length = int(len(audio) / playback_speed)
    audio_stretched = librosa.effects.time_stretch(audio, playback_speed)

    #resampled_audio = resample_poly(audio_stretched, target_length, len(audio_stretched))
    resampled_audio = change_dynamic(audio_stretched, sr)
    return resampled_audio

from funasr import AutoModel

def funasr_ts():
    model = AutoModel(model="fa-zh", model_revision="v2.0.4")
    print("path", model.model_path)
    wav_file = f"{model.model_path}/example/asr_example.wav"
    text_file = f"{model.model_path}/example/text.txt"
    res = model.generate(input=(wav_file, text_file), data_type=("sound", "text"))
    print(res)
    print("len:", len(res[0]["text"].split()), len(res[0]["timestamp"]))
    return res[0]
def fun_para(audio):
    model = AutoModel(model="paraformer-zh", model_revision="v2.0.4",
                      #vad_model="fsmn-vad", vad_model_revision="v2.0.4",
                      #punc_model="ct-punc-c", punc_model_revision="v2.0.4",
                      # spk_model="cam++", spk_model_revision="v2.0.2",
                      )
    audio = np.array(audio)
    print("audio:", audio.shape)
    res = model.generate(input=audio,
                batch_size_s=1,
                hotword='')

    print("len:", len(res[0]["text"].split()), len(res[0]["timestamp"]))# 'timestamp': [[50, 230], [230, 390], [390, 570], unit ms , txt 那 第 三 点 呢
    print(res)
    return res[0]["text"].split(), res[0]["timestamp"]
# type 0-slow [], 1 quick ()
def find_surrounded_words_fun(type, txt_emp, text_asr, timestamp):
    surrounded_words = []
    tasr = copy.deepcopy(text_asr)

    emp1 = ['[','(']
    emp2 = [']', ')']

    start_index = -1
    emtype = 0
    for i in range(len(txt_emp)):
        if txt_emp[i] == emp1[0]:
            start_index = i
            emtype = 0
            print("type0")
        elif txt_emp[i] == emp1[1]:
            start_index = i
            emtype = 1
            print("type1")
        elif txt_emp[i] == emp2[emtype]:
            if start_index != -1:
                surrounded_text = txt_emp[start_index + 1:i]
                words = surrounded_text
                print("words:", words, len(words))
                # find the begin and end of the word
                begin_word = 0
                end_word = 0
                for j in range(len(words)):
                    for k in range(len(tasr)):
                        print("word,itm", words[j], k)
                        if tasr[k] == words[j]:
                            tasr[k] = ''
                            if 0 == j:
                                begin_word = k
                            if len(words) - 1 == j:
                                end_word = k
                            break
                        #
                if end_word == 0:
                    end_word = begin_word
                surrounded_words.append({
                    'word': words,
                    'start': timestamp[begin_word][0],
                    'end': timestamp[end_word][1],
                    "type": emtype
                })
                start_index = -1
        else:
            print("wird startind:", txt_emp[i], start_index)
            if -1 == start_index:
                for k in range(len(tasr)):
                    if tasr[k] == txt_emp[i]:
                        tasr[k] = ''
                        break

    print("final tasr:", tasr)
    return surrounded_words

import pybungee
def change_speed_my(audio, sr, speed):
    outputData = []
    pitch = 0
    print("input len:", len(audio))
    inSampleRate = sr
    outSampleRate = sr
    outputData = pybungee.process(audio, inSampleRate, outputData, outSampleRate, speed, pitch)
    outputData = change_dynamic(outputData, sr)
    print("outlen:", len(outputData))
    return outputData
def emph_fun(txt, audio, denoise):
    sr = 16000
    audio = np.array(audio)
    tasr, ts = fun_para(audio)

    ret_slow = find_surrounded_words_fun(0, txt, tasr, ts)
    print("ret, ", ret_slow)
    #把音频数据按解析后的词分割成多段, sr:16000
    if len(ret_slow) > 0:
        slow_speed = 0.75
        slice_start = 0
        slice_end = 0
        audio_new = []
        print("audio len:", len(audio))
        audio_slow = change_speed_my(audio, sr, slow_speed)
        for itm in ret_slow:
            print("item:", itm)
            slice_end = int(itm['start'] * sr/1000)
            print("111 slicesta,end", slice_start, slice_end)
            audio_new.extend(audio[slice_start:slice_end])
            slice_start = int(itm['end'] * sr/1000)
            print("slice_sta,end:", slice_end, slice_start, audio[slice_end:slice_start])
            if 1 == itm['type']:
                changed_slice = change_speed_my(audio[slice_end:slice_start], sr, 1.23)
            else:
                slice_end_slow = int(slice_end / slow_speed)
                slice_slow_start = int(slice_start / slow_speed)
                changed_slice = audio_slow[slice_end_slow:slice_slow_start]
            audio_new.extend(changed_slice)

        if slice_start != 0:
            audio_new.extend(audio[slice_start:])
        print("finished audio new:",  len(audio_new))
    else:
        audio_new = audio
    #sf.write('newhoas2.wav', audio_new, sr)
    if 0 == denoise:
        audio_d = audio_new
    else:
        audio_d = denoise_wav(audio_new)
    #sf.write('newhoas2_denoised.wav', audio_d, sr)
    return audio_d
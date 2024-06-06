# SynthereTTS: Realistic Chinese speech synthesis 

<br> 
English | [中文](README-ZH.md)
<br> SynthereTTS introduces unique techniques into a simple user interface to provide more realistic speech synthesis and voice cloning applications . 

![mainframe](./resource/main.png) 

<br> 

## Updates 

- 

  

## Features 

Synther TTS has the following features: 

1. **Optional basic and advanced models**: The basic model uses the pre-trained vits model, and the advanced version is built on GPT- On top of the SoVITS model. 

2. **Emphasis can be set**: Use [] to arbitrarily set the words or phrases that need to be emphasized. 

3. **Noise Suppression**: The noise suppression function can adaptively suppress the generated noise and improve the quality of the generated audio. 

4. **Cloning and cross-language speech synthesis**: In addition to training the model through the speaker's voice, you can also directly use the speaker's reference audio that is different from the pre-trained model to synthesize a voice with reference audio timbre. 
5. **Easy to use**: The front-end interface is rewritten using pyqt, which is efficient and eliminates complicated parameter settings. 



## Hardware Requirements 

 Can run on CPU or GPU. The CPU is slower when running the high-end version. If you use GPU to run, you need at least 8GB of video memory; for CPU running, 16G or above is recommended. 



### Supported Languages 

| Language | Status |
| ------- |:---:|
| English (en) | ✅ |
| Chinese (zh) | ✅ |

## FAQ 

#### Where can I download checkpoint? 

* The vits model used in the basic version can be downloaded from the link provided by [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx); the advanced version of the pre-trained model can be downloaded from Download from the link provided in [GPT_SoVITS](https://github.com/RVC-Boss/GPT-SoVITS), or follow the prompts to train your own model. 

#### Can I generate long text? 

* When the text length increases, the generation time of high-order models will increase significantly. Although longer text synthesis can be achieved by modifying the constraints, it is still recommended to split the text into segments. 

#### More... 

## To-do items 
- [ ] Add intonation control 
- [ ] Basic version model adds emphasis and noise suppression 
- [ ] Increase emphasis level, provide hot word mapping with different emphasis levels 
- [ ] More ... 
- [ ] 

## Appreciation 

- [Controllable Emphasis with zero data for text-to-speechr](https://arxiv.org/abs/2307.07062) Insights that emphasize control 
- [sherpa-onnx](https:/ /github.com/k2-fsa/sherpa-onnx) Efficient and easy-to-use VITS model
[GPT_SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) provides an excellent Chinese speech synthesis model
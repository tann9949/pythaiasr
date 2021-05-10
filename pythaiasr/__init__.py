# -*- coding: utf-8 -*-
import torch
from datasets import ClassLabel
from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2ForCTC, Wav2Vec2Processor
import torchaudio
import librosa
import numpy as np

processor = Wav2Vec2Processor.from_pretrained("chompk/wav2vec2-large-xlsr-thai-tokenized")
model = Wav2Vec2ForCTC.from_pretrained("chompk/wav2vec2-large-xlsr-thai-tokenized")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def speech_file_to_array_fn(batch):
    speech_array, sampling_rate = torchaudio.load(batch["path"])
    batch["speech"] = speech_array[0].numpy()
    batch["sampling_rate"] = sampling_rate
    return batch


def resample(batch):
    batch["speech"] = librosa.resample(np.asarray(batch["speech"]), 48_000, 16_000)
    batch["sampling_rate"] = 16_000
    return batch


def prepare_dataset(batch):
    # check that all files have the correct sampling rate
    batch["input_values"] = processor(batch["speech"], sampling_rate=batch["sampling_rate"]).input_values
    return batch


def asr(file: str, show_pad = False):
    b = {}
    b['path'] = file
    a = prepare_dataset(resample(speech_file_to_array_fn(b)))
    input_dict = processor(a["input_values"][0], return_tensors="pt", padding=True)
    logits = model(input_dict.input_values.to(device)).logits
    pred_ids = torch.argmax(logits, dim=-1)[0]
    if show_pad:
        txt = processor.decode(pred_ids)
    else:
        txt = processor.decode(pred_ids).replace('[PAD]','')
    return txt

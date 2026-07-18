# Vienounce Core

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Language: Vietnamese](https://img.shields.io/badge/Readme-🇻🇳-lightgrey.svg)](README.md)
[![Language: English](https://img.shields.io/badge/Readme-🇺🇸-brightgreen.svg)](#)

---

Vienounce Core is an open-source, offline Python library designed to analyze English pronunciation and detect common L1 transfer errors specific to Vietnamese speakers. It uses a unified bilingual phonetic space to align user recordings and generate phone-level Goodness of Pronunciation (GOP) feedback.

---

## 🖥️ Standalone Local Gradio GUI Preview

The package comes with a built-in Gradio dashboard (`gui_local.py`) designed for standalone offline practice. It allows you to enter a target sentence, record your attempt, and view phone-level highlights along with your overall pronunciation score locally:

![Local Gradio GUI Preview](assets/example-local.png)

---

## ☁️ Personalised Cloud Dashboard Preview

In our cloud version, our custom trained model also compares standard native references (Kokoro TTS) to assist learners in hearing L1 transfer differences:

![Personalised Cloud Dashboard Preview](assets/example-cloud.png)

---

## Features

*   **Bilingual Phoneme Mapping**: Seamlessly converts English targets using the bilingual `sea-g2p` phonemizer.
*   **Phone-Level Diagnostics**: Utilizes a Wav2Vec2 acoustic forced-aligner (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`) to align audio to IPA phonemes.
*   **Goodness of Pronunciation (GOP)**: Computes posterior log-probabilities per phoneme to score accuracy.
*   **Standardized Thresholds**: Maps GOP scores to visual markers:
    *   🟢 **Green (Correct)**: $\text{GOP} \ge -2.5$
    *   🟡 **Yellow (Accented/Marginal)**: $-5.0 \le \text{GOP} < -2.5$
    *   🔴 **Red (Dropped/Incorrect)**: $\text{GOP} < -5.0$
*   **Offline-First & CPU-Friendly**: Operates fully locally, loading models on CPU without database or cloud storage dependencies.
*   **Local Gradio GUI**: Interactive web dashboard (`gui_local.py`) to test evaluations on any sentence.

---

## Installation

### Prerequisites
Make sure `ffmpeg` is installed on your system to support audio transcoding:
```bash
# On Ubuntu/Debian:
sudo apt-get install ffmpeg
```

### Setup Virtual Environment
We recommend using `uv` or `pip` in a virtual environment:
```bash
# Clone the repository and navigate to the core directory
cd vienounce-core

# Install in editable mode
pip install -e .
```

---

## Quickstart

### 1. Launch the Standalone GUI Demo
Run the local Gradio interface:
```bash
python gui_local.py
```
Open `http://127.0.0.1:7860` in your web browser, type a target sentence, record your attempt, and click **Diagnose My Pronunciation**.

### 2. Programmatic Usage in Python
You can import `vienounce_core` directly into your custom scripts:

```python
import os
from vienounce_core.models import local_models
from vienounce_core.diagnostics import DiagnosticsService

# 1. Initialize offline model container (loads Wav2Vec2 + sea-g2p)
local_models.initialize()

# 2. Instantiate the Diagnostics Service
diag_service = DiagnosticsService(
    phoneme_model=local_models.phoneme_model,
    feature_extractor=local_models.feature_extractor,
    vocab=local_models.vocab,
    g2p_pipeline=local_models.g2p_pipeline
)

# 3. Diagnose an audio clip against target text
result = diag_service.diagnose_audio(
    user_wav_path="path/to/recording.wav",
    text="I like to eat apples"
)

# 4. View phone scoring metrics
print(f"Overall Score: {result['overall_score']}%")
for word_info in result["words"]:
    print(f"\nWord: {word_info['word']} (Skipped: {word_info['skipped']})")
    for highlight in word_info["highlights"]:
        print(f"  Phone: /{highlight['phone']}/ -> GOP: {highlight['gop']} ({highlight['status']})")
```

---

## Benchmarks

Vienounce Core has been validated against the gold-standard L2-ARCTIC Vietnamese speaker dataset. For detailed evaluation metrics (precision, recall, separation margins) and comparison to custom calibrated models, see [BENCHMARKS.md](BENCHMARKS.md).

---

## Credits & Acknowledgements

*   **Kokoro TTS**: Used to generate standard native English reference tracks. Special thanks to the open-source [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) project.
*   **VieNeu-TTS**: Used to generate Vietnamese-accented English synthesis to highlight L1 transfer differences.

---

## License

This project is licensed under the Apache License 2.0.

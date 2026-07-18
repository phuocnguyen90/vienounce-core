import os
import sys
import re
import json
import urllib.request
import numpy as np
import pandas as pd
import torch
import soundfile as sf
from huggingface_hub import hf_hub_download

# Setup path resolution for local vienounce-core package
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from vienounce_core.diagnostics import DiagnosticsService
from vienounce_core.models import local_models

def download_cmu_arctic_prompts():
    """Download standard CMU ARCTIC prompts list."""
    url = "http://www.festvox.org/cmu_arctic/cmuarctic.data"
    prompts = {}
    try:
        print("Downloading CMU ARCTIC prompt text mappings...")
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
            for line in html.splitlines():
                match = re.match(r'\(\s*(arctic_[ab]\d{4})\s*"(.*)"\s*\)', line)
                if match:
                    prompt_id = match.group(1)
                    text = match.group(2)
                    prompts[prompt_id] = text
        print(f"Successfully downloaded {len(prompts)} prompts.")
    except Exception as e:
        print("Failed to download prompts:", e)
    return prompts

def align_sequences(canonical_list, espeak_list):
    """Align L2-ARCTIC ARPAbet phones with espeak IPA phones."""
    map_arp = {
        'B': 'b', 'D': 'd', 'F': 'f', 'G': 'g', 'HH': 'h', 'JH': 'dʒ',
        'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'P': 'p',
        'R': 'r', 'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'DH': 'ð',
        'V': 'v', 'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
        'AA': 'a', 'AE': 'a', 'AH': 'a', 'AO': 'o', 'AW': 'a', 'AX': 'a',
        'AY': 'a', 'EH': 'e', 'ER': 'e', 'EY': 'e', 'IH': 'i', 'IY': 'i',
        'OW': 'o', 'OY': 'o', 'UH': 'u', 'UW': 'u'
    }
    map_esp = {
        'b': 'b', 'd': 'd', 'f': 'f', 'g': 'g', 'ɡ': 'g', 'h': 'h', 'dʒ': 'dʒ',
        'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'ŋ': 'ŋ', 'p': 'p',
        'r': 'r', 'ɹ': 'r', 's': 's', 'ʃ': 'ʃ', 't': 't', 't̪': 't', 'tʰ': 't', 'θ': 'θ', 'ð': 'ð',
        'v': 'v', 'w': 'w', 'j': 'j', 'z': 'z', 'ʒ': 'ʒ',
        'æ': 'a', 'ʌ': 'a', 'ə': 'a', 'ɔ': 'o', 'ɔː': 'o', 'aɪ': 'a', 'eɪ': 'e', 'ɪ': 'i', 'iː': 'i',
        'oʊ': 'o', 'uː': 'u', 'ʊ': 'u', 'aʊ': 'a', 'e': 'e', 'ɛ': 'e', 'ɑː': 'a', 'ɜː': 'e', 'ɔɪ': 'o'
    }
    
    canonical_mapped = []
    for p in canonical_list:
        clean = ''.join([c for c in p if not c.isdigit()]).strip()
        canonical_mapped.append(map_arp.get(clean, 'x'))
        
    espeak_mapped = []
    for p in espeak_list:
        clean = re.sub(r"[ˈˌːˑ\d\.]", "", p).strip()
        espeak_mapped.append(map_esp.get(clean, 'x'))
        
    import difflib
    matcher = difflib.SequenceMatcher(None, canonical_mapped, espeak_mapped)
    
    esp_to_can = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx in range(i2 - i1):
                esp_to_can[j1 + idx] = i1 + idx
        elif tag == "replace":
            if (i2 - i1) == (j2 - j1):
                for idx in range(i2 - i1):
                    esp_to_can[j1 + idx] = i1 + idx
            else:
                min_len = min(i2 - i1, j2 - j1)
                for idx in range(min_len):
                    esp_to_can[j1 + idx] = i1 + idx
    return esp_to_can

def main():
    print("=" * 80)
    print("VIENOUNCE CORE BASIC MODEL L2-ARCTIC VALIDATION SCRIPT")
    print("=" * 80)

    # 1. Download prompts text list
    prompts = download_cmu_arctic_prompts()
    if not prompts:
        print("❌ Cannot download CMU ARCTIC prompts database.")
        sys.exit(1)

    # 2. Ingest metadata from Hugging Face
    print("\nDownloading L2-ARCTIC metadata...")
    train_metadata_path = hf_hub_download(
        repo_id="vuihocrnd/l2-arctic-cleaned",
        filename="train/metadata.csv",
        repo_type="dataset"
    )
    test_metadata_path = hf_hub_download(
        repo_id="vuihocrnd/l2-arctic-cleaned",
        filename="test/metadata.csv",
        repo_type="dataset"
    )

    df_train = pd.read_csv(train_metadata_path)
    df_test = pd.read_csv(test_metadata_path)

    # Label datasets
    df_train["split"] = "train"
    df_test["split"] = "test"
    df_all = pd.concat([df_train, df_test], ignore_index=True)

    # Extract speaker ID
    df_all["speaker"] = df_all["file_name"].apply(lambda x: x.split('/')[1].split('_')[0])

    # Filter for Vietnamese L1 speakers
    vietnamese_speakers = ["TLV", "TXHC", "THV", "HQTV", "PNV"]
    df_vi = df_all[df_all["speaker"].isin(vietnamese_speakers)].copy()
    print(f"Total Vietnamese speaker rows available: {len(df_vi)}")

    # Sample recordings (20 per speaker to keep it fast but statistically representative)
    sample_size_per_speaker = 20
    sampled_dfs = []
    for sp, group in df_vi.groupby("speaker"):
        sampled_dfs.append(group.sample(n=min(len(group), sample_size_per_speaker), random_state=42))
    df_sampled = pd.concat(sampled_dfs, ignore_index=True)
    print(f"Sampled {len(df_sampled)} total files for core validation.")

    # 3. Initialize local offline core model container
    print("\nInitializing local models...")
    local_models.initialize()
    
    # Initialize basic DiagnosticsService
    diag_service = DiagnosticsService(
        phoneme_model=local_models.phoneme_model,
        feature_extractor=local_models.feature_extractor,
        vocab=local_models.vocab,
        g2p_pipeline=local_models.g2p_pipeline
    )

    validation_data = []

    # 4. Process each sampled WAV file
    for idx, row in df_sampled.iterrows():
        speaker = row["speaker"]
        file_name = row["file_name"]
        split = row["split"]
        label = row["Label"]
        canonical_phones = row["Canonical"].split()
        error_list = eval(row["Error"])
        
        # Determine Hugging Face repository folder path
        hf_filename = f"{split}/{file_name}"
        prompt_id = "_".join(label.split("_")[1:])
        prompt_text = prompts.get(prompt_id, None)

        if not prompt_text:
            continue

        print(f"[{idx+1}/{len(df_sampled)}] Processing {speaker} - {prompt_id}...")

        try:
            # Download audio file locally
            wav_path = hf_hub_download(
                repo_id="vuihocrnd/l2-arctic-cleaned",
                filename=hf_filename,
                repo_type="dataset"
            )

            # Diagnose using the basic core model
            diag_output = diag_service.diagnose_audio(wav_path, prompt_text)

            # Gather espeak phones and GOP scores from diagnostic highlights
            espeak_phones = []
            gop_scores = []
            
            for word_meta in diag_output["words"]:
                if word_meta.get("skipped", False):
                    continue
                for highlight in word_meta["highlights"]:
                    espeak_phones.append(highlight["phone"])
                    gop_scores.append(highlight["gop"])

            # Align espeak phone sequence with L2-ARCTIC canonical sequence
            align_map = align_sequences(canonical_phones, espeak_phones)

            # Store mapping matching GOP against gold-standard phonetic correctness label
            for esp_idx, gop in enumerate(gop_scores):
                if esp_idx in align_map:
                    can_idx = align_map[esp_idx]
                    gold_correct = error_list[can_idx]  # 1 = correct, 0 = error/drop
                    phone = espeak_phones[esp_idx]
                    
                    # We focus on L1-transfer phones
                    clean_phone = re.sub(r"[ˈˌːˑ\d\.]", "", phone).strip()
                    is_critical = clean_phone in ["k", "t", "p", "d", "b", "g", "s", "z", "ʃ", "ʒ", "θ", "ð", "l", "r", "ɹ"]
                    
                    validation_data.append({
                        "speaker": speaker,
                        "prompt_id": prompt_id,
                        "phone": phone,
                        "gop": gop,
                        "gold_correct": gold_correct,
                        "is_critical": is_critical
                    })
        except Exception as e:
            print(f"  ⚠️ Error processing {label}: {e}")

    # 5. Perform validation calculations
    df_val = pd.DataFrame(validation_data)
    if df_val.empty:
        print("❌ No validation data collected.")
        sys.exit(1)

    print("\n" + "="*70)
    print("VIENOUNCE CORE BASIC MODEL L2-ARCTIC VALIDATION STATISTICS")
    print("="*70)

    # Overall distributions
    correct_gops = df_val[df_val["gold_correct"] == 1]["gop"]
    incorrect_gops = df_val[df_val["gold_correct"] == 0]["gop"]

    print(f"Correct Pronunciations Count: {len(correct_gops)} | Mean GOP: {correct_gops.mean():.2f} (Std: {correct_gops.std():.2f})")
    print(f"Incorrect/Dropped Count: {len(incorrect_gops)} | Mean GOP: {incorrect_gops.mean():.2f} (Std: {incorrect_gops.std():.2f})")
    print(f"Separation Margin: {correct_gops.mean() - incorrect_gops.mean():.2f}")

    # Critical phonemes distributions
    df_crit = df_val[df_val["is_critical"]]
    correct_crit = df_crit[df_crit["gold_correct"] == 1]["gop"]
    incorrect_crit = df_crit[df_crit["gold_correct"] == 0]["gop"]

    print(f"\n[Critical Phonemes Only - Coda/Sibilants/Liquids]")
    print(f"Correct Count: {len(correct_crit)} | Mean GOP: {correct_crit.mean():.2f}")
    print(f"Incorrect/Dropped Count: {len(incorrect_crit)} | Mean GOP: {incorrect_crit.mean():.2f}")
    print(f"Critical Separation Margin: {correct_crit.mean() - incorrect_crit.mean():.2f}")

    # Calculate metrics with standard -2.5 threshold for yellow/red detection
    # An error is flagged if GOP < -2.5 (accents & drops are flagged)
    predicted_error = df_crit["gop"] < -2.5
    gold_error = df_crit["gold_correct"] == 0

    tp = np.sum(predicted_error & gold_error)
    fp = np.sum(predicted_error & ~gold_error)
    fn = np.sum(~predicted_error & gold_error)
    tn = np.sum(~predicted_error & ~gold_error)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(df_crit)

    print("\n" + "="*70)
    print("DETECTION PERFORMANCE (Threshold = -2.5)")
    print("="*70)
    print(f"F1-Score: {f1*100:.1f}%")
    print(f"Precision: {precision*100:.1f}%")
    print(f"Recall: {recall*100:.1f}%")
    print(f"Accuracy: {accuracy*100:.1f}%")

    print("\nValidation completed successfully!")

if __name__ == "__main__":
    main()

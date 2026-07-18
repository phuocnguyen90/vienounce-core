import os
import re
import uuid

def split_ipa_to_phones(ipa_str: str) -> list[str]:
    """Split a continuous IPA string into individual phone symbols, keeping digraphs and diphthongs intact."""
    clean_ipa = re.sub(r"[ˈˌːˑ\d\.]", "", ipa_str.strip())
    multis = ["tʃ", "dʒ", "aɪ", "eɪ", "oʊ", "aʊ", "iː", "uː", "ɔː", "ɑː", "ɜː", "pʰ", "tʰ", "kʰ", "t̪"]
    phones = []
    i = 0
    while i < len(clean_ipa):
        matched = False
        for m in multis:
            if clean_ipa[i : i + len(m)] == m:
                phones.append(m)
                i += len(m)
                matched = True
                break
        if not matched:
            phones.append(clean_ipa[i])
            i += 1
    return phones

def align_graphemes_to_phones(word: str, phones_str: str) -> list[tuple[str, list[int]]]:
    """
    Align graphemes (letters) to phonemes using strict orthographic mapping rules.
    """
    word = word.lower()
    phones = [re.sub(r"[ˈˌːˑ\d\.]", "", p) for p in phones_str.strip().split() if p.strip()]

    MAPPING_RULES = {
        # === Digraphs (multi-letter → single phone) ===
        "th": ["θ", "ð"],           # think, this (no /t/, /d/ allowed)
        "sh": ["ʃ"],                # ship (no /s/ allowed)
        "ch": ["tʃ", "k"],          # church, chemistry (no bare /t/)
        "ck": ["k"],                # back, stick
        "ng": ["ŋ"],                # sing (no /n/ allowed)
        "ph": ["f"],                # phone
        "gh": ["f", "g"],           # tough, ghost (silent gh handled by skip logic)
        "wr": ["r"],                # write (silent w)
        "kn": ["n"],                # knife (silent k)
        "mb": ["m"],                # climb (silent b)
        
        # === Consonants (strict, no error-masking) ===
        "c": ["k", "s"],            # cat, city
        "k": ["k"],                 
        "t": ["t", "t̪", "ɾ"],      # Include flap /ɾ/ for "water", "better"
        "d": ["d"],                 # NO /t/ allowed (catches devoicing)
        "p": ["p", "pʰ"],           # Include aspiration variant
        "b": ["b"],                 # NO /p/ allowed (catches devoicing)
        "g": ["g", "ɡ", "dʒ"],      # Unicode variants + "gem" case
        "j": ["dʒ"],                # judge (NO /z/ allowed)
        "s": ["s"],                 # NO /z/, /ʃ/ allowed (catches errors)
        "z": ["z"],                 # NO /s/ allowed (catches plural errors)
        "f": ["f"],                 # NO /v/, /p/ allowed
        "v": ["v"],                 # NO /w/, /f/ allowed
        "l": ["l"],                 # NO /n/ confusion
        "r": ["r", "ɹ"],            # Vietnamese trill + English approximant
        "m": ["m"],
        "n": ["n", "ŋ", "ɲ"],       # can, sink, canyon
        "w": ["w"],
        "h": ["h"],
        "y": ["j"],                 # IPA /j/ for consonantal "y"
        
        # === Vowel Digraphs ===
        "ea": ["iː", "i", "eɪ", "e", "ɛ"],  # meat, bread, break
        "ee": ["iː", "i"],                   # bee
        "oo": ["uː", "u", "ʊ"],              # food, book
        "ou": ["aʊ", "uː", "ʌ", "ə"],       # out, you, touch, famous
        "ow": ["aʊ", "oʊ"],                  # cow, show
        "oa": ["oʊ", "ɔː"],                  # boat, broad
        "ai": ["eɪ", "æ"],                   # rain, said
        "ay": ["eɪ"],                        # day
        "oi": ["ɔɪ"],                        # coin
        "oy": ["ɔɪ"],                        # boy
        "ui": ["uː", "ɪ"],                   # fruit, build
        "ie": ["iː", "aɪ"],                  # field, pie
        "ei": ["eɪ", "iː", "aɪ"],            # vein, ceiling, height
        "ey": ["eɪ", "iː"],                  # they, key
        "igh": ["aɪ"],                       # night
        "au": ["ɔː", "æ"],                   # auto, laugh
        "aw": ["ɔː"],                        # law
        
        # === Single Vowels ===
        "a": ["æ", "eɪ", "A", "ə", "ɔː", "ɑː"], # cat, cake, father, about, all
        "e": ["e", "iː", "ə", "ɪ"],         # bet, be, the, pretty
        "i": ["ɪ", "aɪ", "iː"],              # sit, ice, machine
        "o": ["ɒ", "oʊ", "ʌ", "ɔː", "ə"],   # hot, go, son, for, lemon
        "u": ["ʌ", "juː", "uː", "ʊ", "ə"],  # cup, use, rule, put, upon
        "y": ["aɪ", "ɪ", "iː", "j"],        # my, gym, happy, yes
    }
    
    alignment = []
    w_idx = 0
    p_idx = 0
    
    while p_idx < len(phones):
        phone = phones[p_idx]
        matched = False
        
        # Check digraphs (2 chars)
        if w_idx < len(word) - 1:
            digraph = word[w_idx : w_idx + 2]
            if digraph in MAPPING_RULES and any(phone == rule_p for rule_p in MAPPING_RULES[digraph]):
                alignment.append((phone, [w_idx, w_idx + 1]))
                w_idx += 2
                p_idx += 1
                matched = True
                continue
                
        # Check single letters
        if w_idx < len(word):
            letter = word[w_idx]
            if letter in MAPPING_RULES and any(phone == rule_p for rule_p in MAPPING_RULES[letter]):
                alignment.append((phone, [w_idx]))
                w_idx += 1
                p_idx += 1
                matched = True
                continue
                
        # Skip truly silent letters in spelling
        is_silent_e = (w_idx < len(word) and word[w_idx] == "e" and w_idx == len(word) - 1)
        is_plural_silent_e = (w_idx < len(word) and word[w_idx] == "e" and w_idx == len(word) - 2 and word[-1] == "s")
        is_silent_w = (w_idx < len(word) and word[w_idx] == "w" and w_idx < len(word) - 1 and word[w_idx+1] == "r")
        is_silent_k = (w_idx < len(word) and word[w_idx] == "k" and w_idx < len(word) - 1 and word[w_idx+1] == "n")
        is_silent_b = (w_idx < len(word) and word[w_idx] == "b" and w_idx == len(word) - 1 and w_idx > 0 and word[w_idx-1] == "m")
        is_silent_l = (w_idx < len(word) and word[w_idx] == "l" and w_idx < len(word) - 1 and word[w_idx+1] in ["k", "d"])
        is_silent_h = (w_idx < len(word) and word[w_idx] == "h" and any(word.startswith(x) for x in ["honest", "honor", "honour", "hour", "heir"]))
        is_silent_t = (w_idx < len(word) and word[w_idx] == "t" and ((w_idx > 0 and word[w_idx-1] == "s" and w_idx < len(word) - 1 and word[w_idx+1] in ["e", "l"]) or "often" in word))

        if w_idx < len(word) and (is_silent_e or is_plural_silent_e or is_silent_w or is_silent_k or is_silent_b or is_silent_l or is_silent_h or is_silent_t):
            w_idx += 1
            continue
            
        # Fallback mapping
        if w_idx < len(word):
            alignment.append((phone, [w_idx]))
            w_idx += 1
        else:
            alignment.append((phone, []))
        p_idx += 1
        
    return alignment

def _trim_silence_numpy(y, top_db: float = 25.0, frame_length: int = 2048, hop_length: int = 512):
    """Trim leading and trailing silence using root-mean-square energy thresholding."""
    import numpy as np
    if len(y) == 0:
        return y
    rms = []
    for i in range(0, len(y) - frame_length + 1, hop_length):
        frame = y[i : i + frame_length]
        rms.append(np.sqrt(np.mean(frame ** 2) + 1e-10))
    
    if not rms:
        return y
        
    rms = np.array(rms)
    rms_db = 20 * np.log10(rms / (np.max(rms) + 1e-10))
    
    active_frames = np.where(rms_db > -top_db)[0]
    if len(active_frames) == 0:
        return np.array([], dtype=y.dtype)
        
    start_sample = active_frames[0] * hop_length
    end_sample = min(len(y), active_frames[-1] * hop_length + frame_length)
    
    return y[start_sample:end_sample]

class DiagnosticsService:
    _asr_pipeline = None

    def __init__(self, phoneme_model, feature_extractor, vocab, g2p_pipeline=None, phonetic_asr_model=None):
        self.phoneme_model = phoneme_model
        self.feature_extractor = feature_extractor
        self.vocab = vocab
        self.g2p_pipeline = g2p_pipeline
        self.phonetic_asr_model = phonetic_asr_model
        self.english_lexicon = self._load_english_lexicon()
        
        # Load standard conversational lexicon overrides configuration
        self.lexicon_overrides = {}
        try:
            import os
            import json
            overrides_path = os.getenv("LEXICON_OVERRIDES_PATH") or os.path.join(
                os.path.dirname(__file__), "lexicon_overrides.json"
            )
            if os.path.exists(overrides_path):
                with open(overrides_path, "r", encoding="utf-8") as f:
                    self.lexicon_overrides = json.load(f)
                print(f"[Diagnostics] Loaded {len(self.lexicon_overrides)} lexicon overrides from {overrides_path}")
        except Exception as e:
            print(f"Warning: Failed to load lexicon overrides config: {e}")

        # Apply conversational overrides to standard dictionary
        if isinstance(self.english_lexicon, dict) and self.lexicon_overrides:
            for word, ipa in self.lexicon_overrides.items():
                self.english_lexicon[word.lower().strip()] = ipa.strip()
        
        # Load dynamic GOP calibration configurations
        self.calibration_config = {}
        try:
            import os
            import json
            config_path = os.getenv("GOP_CALIBRATION_PATH") or os.path.join(
                os.path.dirname(__file__), "gop_calibration.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.calibration_config = json.load(f)
                print(f"[Diagnostics] Loaded dynamic GOP calibration from {config_path}")
        except Exception as e:
            print(f"Warning: Failed to load dynamic GOP calibration config: {e}")

    def _load_english_lexicon(self) -> dict:
        """Load standard English IPA lexicon from local cache, downloading from raw public dictionary if not present."""
        import os
        import json
        import urllib.request
        
        cache_dir = os.path.expanduser("~/.cache/vienounce")
        os.makedirs(cache_dir, exist_ok=True)
        json_path = os.path.join(cache_dir, "en_US.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as read_err:
                print(f"Warning: Failed to load cached English lexicon: {read_err}. Re-downloading.")
                
        # Download and parse raw en_US ipa dictionary
        url = "https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/data/en_US.txt"
        txt_path = os.path.join(cache_dir, "en_US.txt")
        try:
            print("Downloading standard English IPA lexicon (ipa-dict)...")
            urllib.request.urlretrieve(url, txt_path)
            
            lexicon = {}
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "\t" not in line:
                        continue
                    parts = line.split("\t")
                    word = parts[0].strip().lower()
                    ipa_raw = parts[1].strip()
                    # Take the first pronunciation option
                    first_option = ipa_raw.split(",")[0].strip()
                    # Strip enclosing slashes '/.../'
                    if first_option.startswith("/") and first_option.endswith("/"):
                        first_option = first_option[1:-1]
                    
                    # Normalize IPA characters to match espeak/sea-g2p phone inventory
                    first_option = first_option.replace("ɝ", "ɚ").replace("ɫ", "l")
                    lexicon[word] = first_option
                    
            # Cache as JSON
            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(lexicon, json_file, ensure_ascii=False)
                
            # Clean up raw txt file to save disk space
            if os.path.exists(txt_path):
                os.remove(txt_path)
                
            return lexicon
        except Exception as dl_err:
            print(f"Warning: Failed to download standard English lexicon: {dl_err}. Falling back to default G2P predictions.")
            return {}

    def map_espeak_phones_to_vocab_tokens(self, phones: list[str]) -> list[int]:
        """Convert standard phone strings to token index integers using Wav2Vec2 espeak dictionary."""
        tokens = []
        
        for p in phones:
            clean_p = p.replace("ː", "").replace("ˈ", "").replace("ˌ", "").replace("ˑ", "").strip()
            if clean_p == "ɫ":
                clean_p = "l"
            if not clean_p:
                continue
            if clean_p in self.vocab:
                val = self.vocab[clean_p]
                tokens.append(val)
            else:
                fallback_found = False
                for char in clean_p:
                    if char in self.vocab:
                        val = self.vocab[char]
                        tokens.append(val)
                        fallback_found = True
                        break
                if not fallback_found:
                    val = self.vocab["<unk>"] if "<unk>" in self.vocab else 1
                    tokens.append(val)
        return tokens

    def diagnose_audio(self, user_wav_path: str, text: str, mock_asr_transcript: str | None = None) -> dict:
        """Run Hybrid ASR-Forced Aligner pipeline: pre-ASR filtering, alignment refinement, and GOP calculations."""
        import torch
        import torchaudio
        import numpy as np

        # Resolve dynamic phoneme mapping function using standard English lexicon lookup with G2P fallback
        g2p_func = None
        if self.g2p_pipeline is not None:
            g2p_func = lambda word: self.english_lexicon.get(word.lower(), self.g2p_pipeline.run(word))
        else:
            try:
                from vieneu_utils.phonemize_text import phonemize_with_dict
                g2p_func = lambda word: self.english_lexicon.get(word.lower(), phonemize_with_dict(f"<en>{word}</en>", skip_normalize=True))
            except ImportError:
                raise RuntimeError("No phonemizer (sea-g2p or vieneu_utils) available for diagnostics.")

        # 1. Check if mock ASR is provided
        if mock_asr_transcript is not None:
            asr_text = mock_asr_transcript
            print(f"DEBUG HYBRID PIPELINE (MOCK): target='{text}' | asr='{asr_text}'")
        else:
            # Lazy initialize Whisper-Base ASR pipeline as a class singleton
            if DiagnosticsService._asr_pipeline is None:
                print("Lazy-loading openai/whisper-base.en ASR model...")
                from transformers import pipeline
                device = "cuda" if torch.cuda.is_available() else "cpu"
                DiagnosticsService._asr_pipeline = pipeline(
                    "automatic-speech-recognition",
                    model="openai/whisper-base.en",
                    device=device
                )
                
            try:
                asr_res = DiagnosticsService._asr_pipeline(user_wav_path)
                asr_text = asr_res.get("text", "")
                print(f"DEBUG HYBRID PIPELINE: target='{text}' | asr='{asr_text}'")
            except Exception as e:
                print(f"⚠️ ASR transcription failed: {e}. Falling back to standard forced-alignment.")
                asr_text = text
            
        # Parse target words and ASR words
        words = re.findall(r"\b[a-zA-Z']+\b", text.lower())
        asr_words = re.findall(r"\b[a-zA-Z']+\b", asr_text.lower())
        
        # 3. Perform word-level difference analysis using SequenceMatcher
        import difflib
        matcher = difflib.SequenceMatcher(None, words, asr_words)
        
        skipped_word_indices = set()
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "delete":
                for idx in range(i1, i2):
                    skipped_word_indices.add(idx)
            elif tag == "replace":
                target_slice = words[i1:i2]
                asr_slice = asr_words[j1:j2]
                used_j = set()
                
                if len(target_slice) == len(asr_slice):
                    pass
                else:
                    for t_idx, t_word in enumerate(target_slice):
                        best_ratio = 0.0
                        best_j_idx = -1
                        for local_j, a_word in enumerate(asr_slice):
                            if local_j in used_j:
                                continue
                            ratio = difflib.SequenceMatcher(None, t_word, a_word).ratio()
                            if ratio > best_ratio:
                                best_ratio = ratio
                                best_j_idx = local_j
                        
                        threshold = 0.3 if len(t_word) <= 3 else 0.5
                        if best_ratio >= threshold:
                            used_j.add(best_j_idx)
                        else:
                            skipped_word_indices.add(i1 + t_idx)
                    
        # 4. Refine target phoneme list (exclude skipped words to prevent alignment shift)
        sentence_phones = []
        words_metadata = []
        
        for idx, w in enumerate(words):
            raw_ipa = g2p_func(w)
            raw_ipa = re.sub(r"[\.]", "", raw_ipa)
            w_phones = split_ipa_to_phones(raw_ipa)
            w_phones_str_spaced = " ".join(w_phones)
            alignment = align_graphemes_to_phones(w, w_phones_str_spaced)
            
            is_skipped = idx in skipped_word_indices
            
            words_metadata.append({
                "word": w,
                "phones": w_phones,
                "alignment": alignment,
                "skipped": is_skipped,
                "phone_offset": len(sentence_phones) if not is_skipped else -1
            })
            
            if not is_skipped:
                sentence_phones.extend(w_phones)
                
        if len(sentence_phones) == 0:
            diagnosed_words = []
            for word_meta in words_metadata:
                word_highlights = []
                all_char_indices = []
                for _, idxs in word_meta["alignment"]:
                    all_char_indices.extend(idxs)
                all_char_indices = sorted(list(set(all_char_indices)))
                
                for p_sym, _ in word_meta["alignment"]:
                    word_highlights.append({
                        "char_indices": all_char_indices,
                        "phone": p_sym,
                        "gop": -10.0,
                        "status": "red"
                    })
                diagnosed_words.append({
                    "word": word_meta["word"],
                    "highlights": word_highlights,
                    "skipped": True
                })
            return {
                "overall_score": 0.0,
                "words": diagnosed_words
            }
            
        # 6. Load and resample audio waveform (16000Hz) using soundfile + librosa
        import soundfile as sf
        import librosa

        transcoded_wav_path = user_wav_path + "_converted.wav"
        import subprocess
        try:
            cmd = ["ffmpeg", "-y", "-i", user_wav_path, "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", transcoded_wav_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(transcoded_wav_path):
                os.replace(transcoded_wav_path, user_wav_path)
        except Exception as ffmpeg_err:
            print(f"Warning: ffmpeg transcoding failed: {ffmpeg_err}. Attempting raw load.")

        try:
            y, sr = sf.read(user_wav_path)
            if len(y.shape) > 1:
                y = y.mean(axis=1)  # Convert to mono
            y = y.astype(np.float32)
            if sr != 16000:
                y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        except Exception as load_err:
            raise RuntimeError(f"Failed to load audio file: {load_err}")
            
        if not hasattr(self, "vad_service") or self.vad_service is None:
            # Load SileroVAD from the core package namespace
            from vienounce_core.vad import SileroVAD
            self.vad_service = SileroVAD()
        y_trimmed = self.vad_service.trim_silence(y)
        waveform = torch.from_numpy(y_trimmed).unsqueeze(0)
        
        # 7. Compute acoustic emissions from phoneme model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.phoneme_model = self.phoneme_model.to(device)
        self.phoneme_model.eval()

        with torch.inference_mode():
            inputs = self.feature_extractor(waveform[0], sampling_rate=16000, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            outputs = self.phoneme_model(**inputs)
            emissions = torch.log_softmax(outputs.logits, dim=-1)
            
        token_indices = self.map_espeak_phones_to_vocab_tokens(sentence_phones)
        targets = torch.tensor(token_indices, dtype=torch.long).to(device)
        
        if len(targets) == 0:
            raise ValueError("Phoneme targets list is empty.")
            
        with torch.inference_mode():
            aligned_tokens, scores = torchaudio.functional.forced_align(
                emissions, targets.unsqueeze(0)
            )
        aligned_tokens = aligned_tokens[0].cpu().numpy()
        scores = scores[0].cpu().numpy()
        
        total_gop = 0.0
        active_phones_count = 0
        diagnosed_words = []
        
        for word_meta in words_metadata:
            word_highlights = []
            if word_meta["skipped"]:
                all_char_indices = []
                for _, idxs in word_meta["alignment"]:
                    all_char_indices.extend(idxs)
                all_char_indices = sorted(list(set(all_char_indices)))
                
                for phone in word_meta["phones"]:
                    word_highlights.append({
                        "char_indices": all_char_indices,
                        "phone": phone,
                        "gop": -10.0,
                        "status": "red"
                    })
                    total_gop += -10.0
                    active_phones_count += 1
                diagnosed_words.append({
                    "word": word_meta["word"],
                    "highlights": word_highlights,
                    "skipped": True
                })
            else:
                word_gops = []
                for local_idx, phone in enumerate(word_meta["phones"]):
                    global_idx = word_meta["phone_offset"] + local_idx
                    target_token_id = token_indices[global_idx]
                    
                    target_frames = np.where(aligned_tokens == target_token_id)[0]
                    if len(target_frames) > 0:
                        gop = float(np.mean(scores[target_frames]))
                    else:
                        gop = -10.0
                        
                    total_gop += gop
                    active_phones_count += 1
                    word_gops.append(gop)
                    
                    if gop >= -2.5:
                        status = "green"
                    elif gop >= -5.0:
                        status = "yellow"
                    else:
                        status = "red"
                        
                    char_indices = []
                    for p_sym, idxs in word_meta["alignment"]:
                        p_sym_clean = re.sub(r"[ˈˌːˑ\d\.]", "", p_sym)
                        phone_clean = re.sub(r"[ˈˌːˑ\d\.]", "", phone)
                        if p_sym_clean == phone_clean:
                            char_indices = idxs
                            break
                            
                    word_highlights.append({
                        "char_indices": char_indices,
                        "phone": phone,
                        "gop": round(gop, 2),
                        "status": status
                    })
                diagnosed_words.append({
                    "word": word_meta["word"],
                    "highlights": word_highlights,
                    "skipped": False
                })
                
        overall_score = round(max(0.0, 100.0 + (total_gop / active_phones_count) * 10.0), 1) if active_phones_count > 0 else 0.0
        
        return {
            "overall_score": overall_score,
            "words": diagnosed_words
        }

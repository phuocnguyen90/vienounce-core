import json
import threading

class LocalModelContainer:
    """Offline, standalone model loader container for Wav2Vec2 diagnostics and sea-g2p."""
    def __init__(self):
        self.g2p_pipeline = None
        self.feature_extractor = None
        self.phoneme_model = None
        self.vocab = None
        self._lock = threading.Lock()

    def initialize(self):
        """Loads diagnostics models offline. Does not connect to GCS buckets or load VieNeu-TTS."""
        with self._lock:
            if self.phoneme_model is not None:
                return  # Already loaded

            print("Loading sea-g2p bilingual phoneme pipeline...")
            from sea_g2p import SEAPipeline
            self.g2p_pipeline = SEAPipeline(lang="vi")

            print("Loading espeak-phoneme Wav2Vec2 diagnostic model...")
            from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC
            from huggingface_hub import hf_hub_download
            
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
                "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
            )
            vocab_path = hf_hub_download(
                repo_id="facebook/wav2vec2-xlsr-53-espeak-cv-ft", 
                filename="vocab.json"
            )
            with open(vocab_path, "r", encoding="utf-8") as f:
                self.vocab = json.load(f)
            self.phoneme_model = Wav2Vec2ForCTC.from_pretrained(
                "facebook/wav2vec2-xlsr-53-espeak-cv-ft"
            )

    @property
    def is_initialized(self) -> bool:
        return self.phoneme_model is not None

# Global singleton instance for local/offline run
local_models = LocalModelContainer()

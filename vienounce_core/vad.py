import os
import urllib.request
import numpy as np
import onnxruntime as ort

class SileroVAD:
    def __init__(self, model_path: str = None):
        if model_path is None:
            home = os.path.expanduser("~")
            model_dir = os.path.join(home, ".cache", "vienounce")
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, "silero_vad.onnx")
            
        self.model_path = model_path
        self._ensure_model_exists()
        
        # Load ONNX session on CPU with 1 thread for lightweight execution
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            self.model_path, 
            sess_options=opts, 
            providers=["CPUExecutionProvider"]
        )
        self.reset_states()

    def _ensure_model_exists(self):
        if not os.path.exists(self.model_path):
            print(f"Downloading Silero VAD ONNX model to {self.model_path}...")
            url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
            try:
                urllib.request.urlretrieve(url, self.model_path)
                print("Download completed successfully.")
            except Exception as e:
                # Try fallback mirror if github is slow/blocked
                print(f"Failed to download from GitHub: {e}. Trying Hugging Face mirror...")
                hf_url = "https://huggingface.co/onnx-community/silero-vad/resolve/main/onnx/model.onnx"
                try:
                    urllib.request.urlretrieve(hf_url, self.model_path)
                    print("Download from Hugging Face completed successfully.")
                except Exception as e2:
                    raise RuntimeError(f"Could not download Silero VAD ONNX model: {e2}")

    def reset_states(self):
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, 64), dtype=np.float32)

    def is_speech(self, chunk: np.ndarray, threshold: float = 0.5) -> bool:
        """
        Evaluate if a 16kHz mono chunk contains active speech.
        `chunk` must be exactly 512 samples.
        """
        assert len(chunk) == 512, "Chunk size must be 512 samples."
        
        sr = np.array(16000, dtype=np.int64)
        x = chunk[None, :].astype(np.float32)
        
        # Prepend the 64-sample context buffer to input
        x_with_context = np.concatenate([self._context, x], axis=1)
        
        inputs = {
            "input": x_with_context,
            "sr": sr,
            "state": self._state
        }
        
        out, self._state = self.session.run(None, inputs)
        
        # Update context buffer with the last 64 samples
        self._context = x_with_context[:, -64:]
        
        prob = float(out[0, 0])
        return prob >= threshold

    def trim_silence(self, y: np.ndarray, threshold: float = 0.5, padding_ms: float = 300.0) -> np.ndarray:
        """
        Trim leading and trailing silence of 16kHz mono float32 waveform using Silero VAD.
        Adds padding_ms before and after active speech to prevent cutting off words.
        """
        if len(y) == 0:
            return y
            
        self.reset_states()
        
        # 16kHz sample rate -> 16 samples per ms
        chunk_size = 512
        padding_samples = int(padding_ms * 16)
        
        active_chunks = []
        
        # Process audio in 512-sample chunks
        for i in range(0, len(y), chunk_size):
            chunk = y[i : i + chunk_size]
            if len(chunk) < chunk_size:
                # Zero-pad final chunk if necessary
                padded_chunk = np.pad(chunk, (0, chunk_size - len(chunk)), mode='constant')
            else:
                padded_chunk = chunk
                
            is_active = self.is_speech(padded_chunk, threshold)
            if is_active:
                active_chunks.append(i // chunk_size)
                
        if not active_chunks:
            return np.array([], dtype=y.dtype)
            
        first_active_chunk = active_chunks[0]
        last_active_chunk = active_chunks[-1]
        
        start_sample = max(0, first_active_chunk * chunk_size - padding_samples)
        end_sample = min(len(y), (last_active_chunk + 1) * chunk_size + padding_samples)
        
        return y[start_sample:end_sample]

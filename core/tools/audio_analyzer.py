import librosa
import numpy as np
import json

def analyze_audio_track(file_path):
    """
    Core Audio Engine: Extracts BPM, beat frames, and estimated Key.
    """
    if not file_path:
        return json.dumps({"status": "error", "message": "No file provided."}, ensure_ascii=False)
        
    try:
        # Load audio (fixed sample rate at 22050Hz for performance)
        y, sr = librosa.load(file_path, sr=22050)
        
        # Extract BPM and beats
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # Extract Chroma for basic key estimation
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # 12-tone scale mapping
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        estimated_key = notes[np.argmax(chroma_mean)]
        
        result = {
            "status": "success",
            "bpm": round(float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo), 2),
            "estimated_key": estimated_key,
            "total_beats": len(beat_times),
            "duration_seconds": round(float(librosa.get_duration(y=y, sr=sr)), 2)
        }
        return json.dumps(result, indent=4, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
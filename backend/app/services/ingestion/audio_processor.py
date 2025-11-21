from faster_whisper import WhisperModel
import logging
from typing import Dict, Any, BinaryIO, Optional, List
from pathlib import Path
import tempfile

from app.config import settings
from app.services.ingestion.text_processor import text_processor

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Service for processing audio files: transcription using Faster Whisper"""
    
    def __init__(self):
        # Force CPU mode for now (CTranslate2 package wasn't compiled with CUDA)
        self.device = "cpu"
        self.compute_type = "int8"
        
        # Lazy load model
        self._model = None
    
    @property
    def model(self):
        """Lazy load Whisper model"""
        if self._model is None:
            logger.info(f"Loading Whisper model on {self.device}...")
            self._model = WhisperModel(
                "base",  # Can be: tiny, base, small, medium, large-v2
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("Whisper model loaded successfully")
        return self._model
    
    async def process_audio(
        self,
        audio_data: BinaryIO,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process audio: transcribe using Whisper
        
        Args:
            audio_data: Binary audio data
            filename: Original filename
            metadata: Optional metadata
            
        Returns:
            Dict with:
                - transcript: Full transcription text
                - segments: List of timestamped segments
                - chunks: Text chunks ready for embedding
                - metadata: Enhanced metadata with language, duration
                - num_chunks: Number of chunks
                - token_count: Total tokens
        """
        try:
            # Save to temporary file (Whisper requires file path)
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_file:
                audio_data.seek(0)
                tmp_file.write(audio_data.read())
                tmp_path = tmp_file.name
            
            logger.info(f"Transcribing audio file: {filename}")
            
            # Transcribe
            segments, info = self.model.transcribe(
                tmp_path,
                beam_size=5,
                word_timestamps=True,
                vad_filter=True  # Voice activity detection
            )
            
            # Collect segments
            transcript_segments = []
            full_transcript = []
            
            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                transcript_segments.append(segment_data)
                full_transcript.append(segment.text.strip())
            
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
            
            # Combine all text
            transcript_text = " ".join(full_transcript)
            
            if not transcript_text.strip():
                transcript_text = "[No speech detected in audio]"
            
            logger.info(f"Transcribed {len(transcript_segments)} segments, {len(transcript_text)} characters")
            
            # Chunk the transcript using existing text processor
            processed = await text_processor.process_text(
                transcript_text,
                metadata or {}
            )
            
            # Enhance metadata
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "language": info.language,
                "language_probability": info.language_probability,
                "duration_seconds": info.duration,
                "num_segments": len(transcript_segments),
                "transcript_length": len(transcript_text)
            })
            
            return {
                "transcript": transcript_text,
                "segments": transcript_segments,
                "chunks": processed["chunks"],
                "metadata": enhanced_metadata,
                "num_chunks": processed["num_chunks"],
                "token_count": processed["token_count"]
            }
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            # Clean up temp file on error
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except:
                pass
            raise Exception(f"Failed to process audio: {str(e)}")
    
    def validate_audio(self, audio_data: BinaryIO, filename: str, max_size_mb: int = 100) -> bool:
        """
        Validate audio file
        
        Args:
            audio_data: Binary audio data
            filename: Original filename
            max_size_mb: Maximum file size in MB
            
        Returns:
            True if valid
        """
        try:
            # Check file size
            audio_data.seek(0, 2)
            file_size = audio_data.tell()
            audio_data.seek(0)
            
            if file_size > max_size_mb * 1024 * 1024:
                raise ValueError(f"Audio file too large. Max size: {max_size_mb}MB")
            
            # Check file extension
            valid_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in valid_extensions:
                raise ValueError(f"Unsupported audio format. Supported: {', '.join(valid_extensions)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            raise ValueError(f"Invalid audio file: {str(e)}")

# Global instance
audio_processor = AudioProcessor()

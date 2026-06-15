import os
import cv2
import base64
import logging
from datetime import datetime
from backend.database.db import DatabaseManager
from backend.database.models import VideoRecord
from backend.groq.provider import get_llm_provider

logger = logging.getLogger(__name__)

def sample_frames(video_path: str, interval_seconds: float = 3.0, max_frames: int = 8) -> list[str]:
    if not os.path.exists(video_path):
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Error opening video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 24.0
        
    frame_interval = int(fps * interval_seconds)
    frame_paths = []
    
    scratch_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scratch", "video_frames")
    os.makedirs(scratch_dir, exist_ok=True)
    
    count = 0
    saved_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % frame_interval == 0:
            frame_name = f"frame_{saved_count}_{os.path.basename(video_path)}.jpg"
            frame_path = os.path.join(scratch_dir, frame_name)
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            saved_count += 1
            if saved_count >= max_frames:
                break
        count += 1
        
    cap.release()
    return frame_paths

async def parse_video_observations(video_path: str, patient_id: str = "patient_001") -> dict:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    filename = os.path.basename(video_path)
    frame_paths = sample_frames(video_path, interval_seconds=3.0, max_frames=5) # Reduced max frames for API
    frame_descriptions = []
    provider = get_llm_provider()
    
    for idx, frame_path in enumerate(frame_paths):
        prompt = "Describe the patient's physical state, posture, movements, or environment shown in this video frame.\n" \
                 "Report observations only; do not attempt to diagnose."
                 
        with open(frame_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        try:
            desc = await provider.generate(prompt=prompt, base64_image=base64_image)
            frame_descriptions.append(f"Frame {idx+1} (approx {idx*3}s): {desc}")
        except Exception as e:
            logger.error(f"Failed to analyze frame {idx+1}: {e}")
        finally:
            try:
                os.remove(frame_path)
            except:
                pass

    observations_text = "\n".join(frame_descriptions)
    
    summary = ""
    if frame_descriptions:
        summary_prompt = f"Here is a chronological list of frame observations from a patient video recording:\n" \
                         f"{observations_text}\n\n" \
                         f"Generate a concise clinical summary describing the patient's movements, gait characteristics, physical behaviors, or posture.\n" \
                         f"STRICT RULE: Generate observations and summaries only. DO NOT diagnose any medical condition.\n" \
                         f"Keep the summary objective, clinical, and precise."
                         
        system_prompt = "You are a clinical movement analyst. Summarize video frame descriptions."
        try:
            summary = await provider.generate(summary_prompt, system_prompt)
        except Exception as e:
            logger.error(f"Failed to summarize video: {e}")
            summary = "Summary generation failed."
    else:
        summary = "No frames could be extracted from the video."
        observations_text = "No frame observations."

    timestamp = datetime.utcnow().isoformat()
    record = VideoRecord(
        patient_id=patient_id,
        timestamp=timestamp,
        video_path=video_path,
        summary=summary,
        observations=observations_text
    )
    DatabaseManager.insert_video(record)

    return {
        "filename": filename,
        "summary": summary,
        "observations": observations_text,
        "timestamp": timestamp,
        "video_path": video_path
    }

import os
from datetime import datetime
import cv2
from backend.database.db import DatabaseManager
from backend.database.models import VideoRecord
from backend.rag.ollama_client import query_llava_image, query_ollama_text

def sample_frames(video_path: str, interval_seconds: float = 3.0, max_frames: int = 8) -> list[str]:
    """
    Samples frames from a video file at a given interval.
    Saves frames as temporary images and returns their paths.
    """
    if not os.path.exists(video_path):
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 24.0  # fallback
        
    frame_interval = int(fps * interval_seconds)
    frame_paths = []
    
    # Store frames in the project scratch folder
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
    print(f"Sampled {len(frame_paths)} frames from {os.path.basename(video_path)}")
    return frame_paths

def parse_video_observations(video_path: str, patient_id: str = "patient_001") -> dict:
    """
    Ingests a video file (e.g. gait video, patient behavior video):
    1. Sample frames using OpenCV.
    2. Pass each frame to LLaVA for raw visual observations.
    3. Feed all frame observations to Qwen2.5:7B to generate a unified summary.
    4. Store results in SQLite 'videos' table.
    5. Clean up temporary frame files.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    filename = os.path.basename(video_path)
    
    # 1. Sample frames
    frame_paths = sample_frames(video_path, interval_seconds=3.0, max_frames=8)
    
    frame_descriptions = []
    
    # 2. Query LLaVA for each frame
    for idx, frame_path in enumerate(frame_paths):
        prompt = "Describe the patient's physical state, posture, movements, or environment shown in this video frame.\n" \
                 "Report observations only; do not attempt to diagnose."
        print(f"Analyzing frame {idx+1}/{len(frame_paths)}...")
        desc = query_llava_image(frame_path, prompt)
        frame_descriptions.append(f"Frame {idx+1} (approx {idx*3}s): {desc}")
        
        # Clean up the frame image immediately after querying to save space
        try:
            os.remove(frame_path)
        except Exception as e:
            print(f"Error removing temporary frame {frame_path}: {e}")

    # Combine observations
    observations_text = "\n".join(frame_descriptions)
    
    # 3. Generate summary using Qwen2.5:7B
    summary = ""
    if frame_descriptions:
        summary_prompt = f"Here is a chronological list of frame observations from a patient video recording:\n" \
                         f"{observations_text}\n\n" \
                         f"Generate a concise clinical summary describing the patient's movements, gait characteristics, physical behaviors, or posture.\n" \
                         f"STRICT RULE: Generate observations and summaries only. DO NOT diagnose any medical condition.\n" \
                         f"Keep the summary objective, clinical, and precise."
                         
        system_prompt = "You are a clinical movement analyst. Summarize video frame descriptions."
        summary = query_ollama_text(summary_prompt, system_prompt)
        print(f"Video Summary: {summary[:200]}...")
    else:
        summary = "No frames could be extracted from the video."
        observations_text = "No frame observations."

    # 4. Store in SQLite
    timestamp = datetime.utcnow().isoformat()
    record = VideoRecord(
        patient_id=patient_id,
        timestamp=timestamp,
        video_path=video_path,
        summary=summary,
        observations=observations_text
    )
    DatabaseManager.insert_video(record)
    print(f"Stored video observations in SQLite for {filename}.")

    return {
        "filename": filename,
        "summary": summary,
        "observations": observations_text,
        "timestamp": timestamp,
        "video_path": video_path
    }

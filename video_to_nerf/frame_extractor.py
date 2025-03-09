# video_to_nerf/frame_extractor.py
import os
import subprocess
import logging

class FrameExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(self, video_path, output_dir, fps):
        """
        Extract frames from a video file
        
        Args:
            video_path (str): Path to video file
            output_dir (str): Directory to save frames
            fps (str): Frames per second to extract
            
        Returns:
            tuple: (success, message, num_frames)
        """
        try:
            # Create output directory if it doesn't exist
            images_dir = os.path.join(output_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # Run FFmpeg command
            cmd = [
                "ffmpeg", "-i", video_path, 
                "-r", fps, 
                "-q:v", "1",  # High quality
                os.path.join(images_dir, "frame_%04d.jpg")
            ]
            
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                num_frames = len([f for f in os.listdir(images_dir) if f.endswith('.jpg')])
                return True, "", num_frames
            else:
                return False, stderr.decode(), 0
                
        except Exception as e:
            self.logger.error(f"Frame extraction error: {str(e)}")
            return False, str(e), 0
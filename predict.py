from cog import BasePredictor, Input, Path
import subprocess
import os
import zipfile
import requests
import shutil
import tempfile

class Predictor(BasePredictor):
    def predict(self,
                frames_zip: Path = Input(description="ZIP file containing frames", default=None),
                frames_urls: str = Input(description="Newline-separated URLs of frames to combine into a video", default=None),
                fps: float = Input(description="Number of frames per second of video", default=24.0, ge=1.0),
    ) -> Path:
        """Run ffmpeg to combine frames into a video"""
        temp_folder_path = tempfile.mkdtemp()

        if frames_zip is not None:
            with zipfile.ZipFile(frames_zip, 'r') as zip_ref:
                zip_ref.extractall(f"{temp_folder_path}/frames")

            frame_files = sorted(os.listdir(f"/{temp_folder_path}/frames"))
            for i, frame_file in enumerate(frame_files):
                os.rename(os.path.join(f"{temp_folder_path}/frames", frame_file), f"{temp_folder_path}/frames/out{i:03d}.png")

        elif frames_urls is not None:
            url_list = frames_urls.split('\n')
            for i, url in enumerate(url_list):
                response = requests.get(url, stream=True)
                response.raise_for_status()

                with open(f"{temp_folder_path}/frames/out{i:03d}.png", 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)

        else:
            raise ValueError("Must provide either frames_zip or frames_urls")

        video = f"{temp_folder_path}/out.mp4"
        command = f"ffmpeg -r {fps} -i {temp_folder_path}/frames/out%03d.png -c:v libx264 -vf 'fps={fps},format=yuv420p' {video}"

        subprocess.run(command, shell=True, check=True)

        return Path(video)

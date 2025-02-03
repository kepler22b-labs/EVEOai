import os
import subprocess
from moviepy import VideoFileClip
from pydub import AudioSegment
import numpy as np

def convert_audio_codec(input_video_file, output_video_file):
    """
    Converts the audio codec of the input video file to MP3.
    If the output file already exists, it will be deleted.
    """
    if os.path.exists(output_video_file):
        os.remove(output_video_file)  # Remove existing file

    command = [
        'ffmpeg',
        '-i', input_video_file,
        '-c:v', 'copy',  # Copy the video stream without re-encoding
        '-c:a', 'mp3',   # Convert audio to MP3
        output_video_file
    ]
    
    # Execute the command
    subprocess.run(command, check=True)

def get_audio_intensity(audio_file):
    """
    This function analyzes the audio file and returns the intensity of the audio
    over time in chunks (e.g., every 100ms).
    """
    sound = AudioSegment.from_file(audio_file)
    # Split the audio into chunks (100ms each)
    chunk_length_ms = 100  # 100 milliseconds
    chunks = [sound[i:i + chunk_length_ms] for i in range(0, len(sound), chunk_length_ms)]
    
    intensities = []
    
    for chunk in chunks:
        # Convert the audio chunk into a numpy array of samples
        samples = np.array(chunk.get_array_of_samples())
        
        # Skip empty chunks
        if len(samples) == 0:
            continue
        
        # Ensure samples are treated as floats for RMS calculation
        samples = samples.astype(np.float32)
        
        # Calculate RMS (Root Mean Square) to get intensity of the chunk
        mean_value = np.mean(samples**2)
        
        # Handle negative mean values or NaN
        if mean_value < 0:
            print(f"Invalid mean value encountered: {mean_value}")
            continue
        
        rms = np.sqrt(mean_value)
        
        # Append only if rms is not NaN
        if not np.isnan(rms):
            intensities.append(rms)
    
    return intensities

def create_video_clip(video_file, start_time, duration, output_filename):
    """
    This function creates a video clip starting from start_time and lasting for duration
    and saves it as output_filename.
    """
    video = VideoFileClip(video_file)
    clip = video.subclip(start_time, start_time + duration)
    clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")

def process_video(input_video_file, threshold, clip_duration=60):
    """
    This function processes the video and creates 1-minute clips based on audio intensity.
    It will save the clips in a folder named 'output_clips'.
    """
    # Create output directory
    output_dir = "output_clips"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Temporary file for converted video
    converted_video_file = "temp_converted_video.mp4"
    
    # Convert audio codec to MP3
    convert_audio_codec(input_video_file, converted_video_file)

    # Extract the audio from the converted video
    audio_file = "temp_audio.wav"
    
    video = VideoFileClip(converted_video_file)
    
    # Ensure proper cleanup by waiting for all processes to finish before writing audio
    video.audio.write_audiofile(audio_file)

    # Get the audio intensity values
    intensities = get_audio_intensity(audio_file)

    start_time = 0
    clip_count = 0
    
    # Process the audio and create video clips based on intensity
    for i in range(0, len(intensities), clip_duration * 10):  # Each chunk represents 100ms, so 10 chunks = 1 second
        # Calculate average intensity in the 1-minute window
        avg_intensity = np.mean(intensities[i:i + clip_duration * 10])
        
        if avg_intensity > threshold:
            clip_count += 1
            output_filename = os.path.join(output_dir, f"clip_{clip_count}.mp4")
            create_video_clip(converted_video_file, start_time, clip_duration, output_filename)
        
        start_time += clip_duration  # Move to the next minute
    
    # Clean up temporary files after all processing is done
    os.remove(audio_file)
    
    try:
        os.remove(converted_video_file)
    except PermissionError:
        print(f"Could not delete {converted_video_file}. It may still be in use.")

# Example usage
if __name__ == "_main_":
    input_video_file = "pubg.mp4"  # Input video file path
    threshold = 300  # Set the sound intensity threshold value
    process_video(input_video_file, threshold)

from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip

def add_watermark_to_video(video_path: str, watermark_path: str, output_path: str, position=("right", "bottom")):
    """
    Adds an image watermark to a video.
    """
    video_clip = VideoFileClip(video_path)
    watermark_clip = ImageClip(watermark_path).set_duration(video_clip.duration)
    
    # Resize watermark if needed
    watermark_clip = watermark_clip.resize(height=50) # example resize

    final_clip = CompositeVideoClip([video_clip, watermark_clip.set_position(position)])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    video_clip.close()
    final_clip.close()

def add_text_watermark_to_video(video_path: str, text: str, output_path: str, position=("center", "center"), fontsize=50, color='white'):
    """
    Adds a text watermark to a video.
    """
    video_clip = VideoFileClip(video_path)
    
    text_clip = TextClip(text, fontsize=fontsize, color=color).set_duration(video_clip.duration)
    
    final_clip = CompositeVideoClip([video_clip, text_clip.set_position(position)])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video_clip.close()
    final_clip.close()


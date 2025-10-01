from moviepy.editor import VideoFileClip, vfx


# FadeIn
def fadein_transition(clip, t: float):
    return clip.fadein(t)


# FadeOut
def fadeout_transition(clip, t: float):
    return clip.fadeout(t)


# SlideIn
def slidein_transition(clip, t: float, side: str):
    # moviepy 1.0.3에서는 fx 메소드를 사용
    return clip.fx(vfx.slide_in, t, side)


# SlideOut
def slideout_transition(clip, t: float, side: str):
    # moviepy 1.0.3에서는 fx 메소드를 사용
    return clip.fx(vfx.slide_out, t, side)
#!/usr/bin/env python3
"""
Shorts Factory GUI
유튜브 쇼츠 자동화 데스크탑 앱
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import subprocess
import sys
import os

# 경로 설정
APP_DIR = Path(__file__).parent.absolute()
SCRIPTS_PATH = APP_DIR / "templates" / "stoic" / "scripts_premium.json"
OUTPUT_DIR = APP_DIR / "output"


class ShortsFactoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shorts Factory - 스토아 철학 쇼츠")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a2e")

        # 스타일 설정
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # 데이터
        self.scripts = []
        self.selected_script = None
        self.audio_path = None

        # UI 구성
        self.create_widgets()
        self.load_scripts()

    def configure_styles(self):
        """스타일 설정"""
        self.style.configure("Title.TLabel",
                            font=("맑은 고딕", 24, "bold"),
                            foreground="#eee",
                            background="#1a1a2e")
        self.style.configure("Subtitle.TLabel",
                            font=("맑은 고딕", 11),
                            foreground="#888",
                            background="#1a1a2e")
        self.style.configure("TFrame", background="#1a1a2e")
        self.style.configure("Card.TFrame", background="#16213e")
        self.style.configure("TLabel",
                            font=("맑은 고딕", 10),
                            foreground="#eee",
                            background="#16213e")
        self.style.configure("TButton",
                            font=("맑은 고딕", 11, "bold"),
                            padding=10)
        self.style.configure("Accent.TButton",
                            font=("맑은 고딕", 12, "bold"),
                            padding=15)
        self.style.map("Accent.TButton",
                      background=[('active', '#e94560'), ('!active', '#0f3460')])

    def create_widgets(self):
        """위젯 생성"""
        # 메인 컨테이너
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 타이틀
        title_frame = ttk.Frame(main_frame, style="TFrame")
        title_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(title_frame,
                 text="Shorts Factory",
                 style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(title_frame,
                 text="스토아 철학 쇼츠 자동화",
                 style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(15, 0), pady=(10, 0))

        # 좌우 분할
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 왼쪽: 스크립트 목록
        left_frame = ttk.Frame(content_frame, style="Card.TFrame")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        ttk.Label(left_frame,
                 text="스크립트 선택",
                 font=("맑은 고딕", 12, "bold")).pack(pady=10)

        # 리스트박스
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.script_listbox = tk.Listbox(
            list_frame,
            font=("맑은 고딕", 10),
            bg="#0f3460",
            fg="#eee",
            selectbackground="#e94560",
            selectforeground="#fff",
            borderwidth=0,
            highlightthickness=0
        )
        self.script_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.script_listbox.bind('<<ListboxSelect>>', self.on_script_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                  command=self.script_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.script_listbox.config(yscrollcommand=scrollbar.set)

        # 오른쪽: 미리보기 및 컨트롤
        right_frame = ttk.Frame(content_frame, style="Card.TFrame")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        ttk.Label(right_frame,
                 text="스크립트 미리보기",
                 font=("맑은 고딕", 12, "bold")).pack(pady=10)

        # 미리보기 텍스트
        self.preview_text = scrolledtext.ScrolledText(
            right_frame,
            font=("맑은 고딕", 11),
            bg="#0f3460",
            fg="#eee",
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0,
            height=12
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 구분선
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        # 오디오 선택
        audio_frame = ttk.Frame(right_frame, style="Card.TFrame")
        audio_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(audio_frame,
                 text="녹음 파일:",
                 font=("맑은 고딕", 10, "bold")).pack(side=tk.LEFT)

        self.audio_label = ttk.Label(audio_frame,
                                     text="선택 안됨",
                                     font=("맑은 고딕", 10))
        self.audio_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(audio_frame,
                  text="파일 선택",
                  command=self.select_audio).pack(side=tk.RIGHT)

        # 버튼들
        button_frame = ttk.Frame(right_frame, style="Card.TFrame")
        button_frame.pack(fill=tk.X, padx=10, pady=20)

        ttk.Button(button_frame,
                  text="스크립트 복사",
                  command=self.copy_script).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame,
                  text="TTS 텍스트 저장",
                  command=self.save_tts_text).pack(side=tk.LEFT, padx=5)

        self.generate_btn = ttk.Button(
            button_frame,
            text="영상 생성",
            style="Accent.TButton",
            command=self.generate_video
        )
        self.generate_btn.pack(side=tk.RIGHT, padx=5)

        # 상태바
        self.status_var = tk.StringVar(value="준비됨")
        status_bar = ttk.Label(main_frame,
                              textvariable=self.status_var,
                              font=("맑은 고딕", 9),
                              foreground="#888",
                              background="#1a1a2e")
        status_bar.pack(fill=tk.X, pady=(10, 0))

        # 진행바
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(5, 0))

    def load_scripts(self):
        """스크립트 로드"""
        try:
            with open(SCRIPTS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scripts = data.get('scripts', [])

            for script in self.scripts:
                quote = script.get('quote', '')[:40]
                author = script.get('author', '')
                self.script_listbox.insert(tk.END, f"#{script['id']} {quote}... - {author}")

            self.status_var.set(f"{len(self.scripts)}개 스크립트 로드됨")
        except Exception as e:
            messagebox.showerror("오류", f"스크립트 로드 실패: {e}")

    def on_script_select(self, event):
        """스크립트 선택 시"""
        selection = self.script_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        self.selected_script = self.scripts[idx]

        # 미리보기 업데이트
        self.preview_text.delete(1.0, tk.END)

        script = self.selected_script['script']
        preview = f"""[훅]
{script['hook']}

[명언]
{script['quote_read']}

[해설]
{script['explanation']}

[CTA]
{script['cta']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
예상 길이: {self.selected_script.get('duration_estimate', '25-30초')}
"""
        self.preview_text.insert(tk.END, preview)
        self.status_var.set(f"선택됨: #{self.selected_script['id']} - {self.selected_script['author']}")

    def select_audio(self):
        """오디오 파일 선택"""
        filepath = filedialog.askopenfilename(
            title="녹음 파일 선택",
            filetypes=[
                ("오디오 파일", "*.mp3 *.wav *.m4a *.ogg"),
                ("모든 파일", "*.*")
            ]
        )
        if filepath:
            self.audio_path = Path(filepath)
            self.audio_label.config(text=self.audio_path.name)
            self.status_var.set(f"오디오 선택됨: {self.audio_path.name}")

    def copy_script(self):
        """스크립트 클립보드 복사"""
        if not self.selected_script:
            messagebox.showwarning("경고", "먼저 스크립트를 선택하세요")
            return

        tts_text = self.selected_script.get('tts_text', '')
        self.root.clipboard_clear()
        self.root.clipboard_append(tts_text)
        self.status_var.set("스크립트가 클립보드에 복사되었습니다")
        messagebox.showinfo("완료", "스크립트가 클립보드에 복사되었습니다!\n녹음 시 참고하세요.")

    def save_tts_text(self):
        """TTS 텍스트 파일로 저장"""
        if not self.selected_script:
            messagebox.showwarning("경고", "먼저 스크립트를 선택하세요")
            return

        filepath = filedialog.asksaveasfilename(
            title="TTS 텍스트 저장",
            defaultextension=".txt",
            initialfile=f"script_{self.selected_script['id']}.txt",
            filetypes=[("텍스트 파일", "*.txt")]
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.selected_script.get('tts_text', ''))
            self.status_var.set(f"저장됨: {filepath}")
            messagebox.showinfo("완료", f"저장되었습니다:\n{filepath}")

    def generate_video(self):
        """영상 생성"""
        if not self.selected_script:
            messagebox.showwarning("경고", "먼저 스크립트를 선택하세요")
            return

        if not self.audio_path or not self.audio_path.exists():
            messagebox.showwarning("경고", "녹음 파일을 선택하세요")
            return

        # 생성 시작
        self.generate_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("영상 생성 중...")

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=self._generate_video_thread)
        thread.daemon = True
        thread.start()

    def _generate_video_thread(self):
        """영상 생성 스레드"""
        try:
            from core.video_composer import VideoComposer, CompositionConfig
            from core.broll_selector import BrollSelector

            # 설정
            config = CompositionConfig()
            composer = VideoComposer(config)

            # B-roll 선택
            broll_selector = BrollSelector(assets_path=APP_DIR / "assets" / "b-roll")
            broll_clips = broll_selector.select(["nature", "city", "abstract"], target_duration=30.0)

            # 출력 경로
            output_name = f"shorts_{self.selected_script['id']}_{self.selected_script['author']}.mp4"
            output_path = OUTPUT_DIR / output_name
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # 자막 생성
            srt_path = OUTPUT_DIR / f"temp_srt_{self.selected_script['id']}.srt"
            self._create_srt(srt_path)

            # BGM
            bgm_path = APP_DIR / "assets" / "bgm" / "sample_ambient.mp3"
            if not bgm_path.exists():
                bgm_path = None

            # 영상 합성
            result = composer.compose(
                audio_path=self.audio_path,
                broll_clips=broll_clips,
                srt_path=srt_path,
                bgm_path=bgm_path,
                output_path=output_path
            )

            # 완료
            self.root.after(0, lambda: self._on_generate_complete(result))

        except Exception as e:
            self.root.after(0, lambda: self._on_generate_error(str(e)))

    def _create_srt(self, srt_path: Path):
        """SRT 자막 파일 생성"""
        script = self.selected_script['script']

        # 간단한 타이밍 (실제로는 오디오 분석 필요)
        srt_content = f"""1
00:00:00,000 --> 00:00:03,000
{script['hook']}

2
00:00:03,500 --> 00:00:08,500
{script['quote_read']}

3
00:00:09,000 --> 00:00:21,000
{script['explanation']}

4
00:00:21,500 --> 00:00:25,000
{script['cta']}
"""
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

    def _on_generate_complete(self, output_path):
        """생성 완료"""
        self.progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_var.set(f"완료: {output_path}")

        result = messagebox.askyesno(
            "완료",
            f"영상이 생성되었습니다!\n\n{output_path}\n\n폴더를 열까요?"
        )
        if result:
            if sys.platform == 'win32':
                os.startfile(OUTPUT_DIR)
            elif sys.platform == 'darwin':
                subprocess.run(['open', OUTPUT_DIR])
            else:
                subprocess.run(['xdg-open', OUTPUT_DIR])

    def _on_generate_error(self, error):
        """생성 오류"""
        self.progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_var.set("오류 발생")
        messagebox.showerror("오류", f"영상 생성 실패:\n{error}")


def main():
    root = tk.Tk()

    # 아이콘 설정 (있으면)
    try:
        icon_path = APP_DIR / "assets" / "icon.ico"
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
    except:
        pass

    app = ShortsFactoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

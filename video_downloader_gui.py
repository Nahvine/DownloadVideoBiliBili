
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import subprocess
import shutil
import re
import os
import platform
import hashlib
from datetime import datetime
import capcut_utils

# ── Apple Design Philosophy ─────────────────────────────
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

BBDOWN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BBDown")

# ── BBDown quality map  (English UI → BBDown Chinese flag) ─────────────
QUALITY_BBDOWN_MAP = {
    "8K Ultra HD":        "8K 超高清",
    "4K Super HD":        "4K 超清",
    "1080P High Bitrate": "1080P 高码率",
    "1080P HD":           "1080P 高清",
    "720P HD":            "720P 高清",
    "480P SD":            "480P 清晰",
    "360P Low":           "360P 流畅",
}

# ── yt-dlp quality map  (English UI → format string) ────────────────────
QUALITY_YTDLP_MAP = {
    "8K Ultra HD":        "bestvideo[height<=4320]+bestaudio/best",
    "4K Super HD":        "bestvideo[height<=2160]+bestaudio/best",
    "1080P High Bitrate": "bestvideo[height<=1080][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
    "1080P HD":           "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720P HD":            "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480P SD":            "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360P Low":           "bestvideo[height<=360]+bestaudio/best[height<=360]",
}

# ── BBDown piped output → Vietnamese status ─────────────────────────────
BBDOWN_STATUS_MAP = [
    ("开始下载P1视频",  "⬇  Đang tải video..."),
    ("开始下载P1音频",  "⬇  Đang tải audio..."),
    ("开始下载",        "⬇  Đang bắt đầu tải..."),
    ("合并视频分片",    "🔀  Ghép segments video..."),
    ("合并音频分片",    "🔀  Ghép segments audio..."),
    ("开始合并音视频",  "🎬  Đang mux video + audio..."),
    ("下载P1完毕",      "✓   Tải xong, đang xử lý..."),
    ("清理临时文件",    "🧹  Dọn file tạm..."),
    ("任务完成",        "✅  Hoàn thành!"),
    ("视频标题",        None),   # special: extract title
    ("获取视频信息",    "🔍  Đang lấy thông tin video..."),
    ("开始解析",        "🔍  Đang phân tích..."),
]

# ── Vocal Remover models ─────────────────────────────────────────────────
VOCAL_MODELS = {
    "⭐ Best Quality  (UVR-MDX-NET-Inst_HQ_4)": "UVR-MDX-NET-Inst_HQ_4.onnx",
    "⚡ Balanced  (UVR-MDX-NET-Inst_3)":        "UVR-MDX-NET-Inst_3.onnx",
    "🎸 Complex Music  (Demucs htdemucs_ft)":   "htdemucs_ft",
}

def detect_platform(url: str) -> str:
    u = url.lower()
    if "bilibili.com" in u or "b23.tv" in u:
        return "bilibili"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "tiktok.com" in u:
        return "tiktok"
    return "other"


def sanitize(name: str, max_len=50) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', name).replace(' ', '_')[:max_len]


def _is_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "arm64"


# ============================================================
class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Video Downloader Pro")
        self.geometry("600x720")
        self.resizable(False, False)

        self._busy = False
        self._vocal_busy = False

        # Shared output folder across both tabs
        self.output_folder_var = ctk.StringVar(
            value=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self._build_ui()
        self._check_tools()

    # ── UI Construction ──────────────────────────────────────
    def _build_ui(self):
        # App title
        ctk.CTkLabel(self, text="Video Downloader Pro",
                     font=("SF Pro Display", 24, "bold"),
                     text_color=("gray15", "gray92")).pack(pady=(22, 2))
        ctk.CTkLabel(self, text="Bilibili • YouTube • TikTok  +  Vocal Remover",
                     font=("SF Pro Text", 12),
                     text_color=("gray50", "gray65")).pack(pady=(0, 10))

        # ── Tab View ─────────────────────────────────────────
        self.tabs = ctk.CTkTabview(self, width=570, height=610,
                                   corner_radius=14,
                                   fg_color=("gray97", "gray15"),
                                   segmented_button_fg_color=("gray88", "gray22"),
                                   segmented_button_selected_color="#007AFF",
                                   segmented_button_selected_hover_color="#005EC4",
                                   segmented_button_unselected_color=("gray88", "gray22"),
                                   segmented_button_unselected_hover_color=("gray80", "gray30"),
                                   text_color=("gray10", "gray90"),
                                   text_color_disabled=("gray50", "gray55"))
        self.tabs.pack(padx=14, pady=(0, 12), fill="both", expand=True)

        self.tabs.add("⬇  Download")
        self.tabs.add("🎤  Vocal Remover")

        self._build_download_tab(self.tabs.tab("⬇  Download"))
        self._build_vocal_tab(self.tabs.tab("🎤  Vocal Remover"))

    # ══════════════════════════════════════════════════════════
    #   DOWNLOAD TAB
    # ══════════════════════════════════════════════════════════
    def _build_download_tab(self, parent):
        # URL input
        ctk.CTkLabel(parent, text="Video URL",
                     font=("SF Pro Text", 13, "bold"),
                     text_color=("gray30", "gray75")).pack(anchor="w", padx=20, pady=(14, 2))

        self.url_entry = ctk.CTkEntry(
            parent, placeholder_text="Paste video URL here...",
            width=520, height=44, font=("SF Pro Text", 14),
            border_width=1, corner_radius=10, fg_color=("white", "gray20"))
        self.url_entry.pack(pady=(0, 2), padx=20)
        self.url_entry.bind("<KeyRelease>", self._on_url_change)

        self.platform_label = ctk.CTkLabel(parent, text="",
                                           font=("SF Pro Text", 12),
                                           text_color=("gray50", "gray60"))
        self.platform_label.pack(pady=(0, 8))

        # Action buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(pady=4)

        self.download_btn = ctk.CTkButton(
            btn_frame, text="⬇  Download Video",
            font=("SF Pro Text", 14, "bold"), width=180, height=42,
            corner_radius=21, fg_color="#007AFF", hover_color="#005EC4",
            command=self.start_download)
        self.download_btn.pack(side="left", padx=6)

        self.thumb_btn = ctk.CTkButton(
            btn_frame, text="🖼  Thumbnail",
            font=("SF Pro Text", 14, "bold"), width=140, height=42,
            corner_radius=21, fg_color="transparent", border_width=2,
            border_color="#007AFF", text_color=("gray15", "gray90"),
            hover_color=("gray90", "gray25"), command=self.start_thumbnail)
        self.thumb_btn.pack(side="left", padx=6)

        self.capcut_btn = ctk.CTkButton(
            btn_frame, text="🎞  CapCut SRT",
            font=("SF Pro Text", 14, "bold"), width=140, height=42,
            corner_radius=21, fg_color="transparent", border_width=2,
            border_color="#FF9500", text_color=("gray15", "gray90"),
            hover_color=("gray90", "gray25"),
            command=self.start_capcut_extraction)
        self.capcut_btn.pack(side="left", padx=6)

        # Progress + status
        self.progress = ctk.CTkProgressBar(
            parent, width=520, height=5, corner_radius=3,
            progress_color="#007AFF", mode="indeterminate")
        self.progress.pack(pady=6)
        self.progress.pack_forget()

        self.status_label = ctk.CTkLabel(
            parent, text="Ready ✓",
            font=("SF Pro Text", 12), text_color=("gray45", "gray60"))
        self.status_label.pack(pady=(0, 4))

        # Divider
        ctk.CTkFrame(parent, height=1, width=520,
                     fg_color=("gray82", "gray32")).pack(pady=10)

        # Settings panel
        self._build_settings_panel(parent)

        # Footer note
        ctk.CTkLabel(
            parent,
            text="Bilibili → BBDown (no watermark)   •   Others → yt-dlp",
            font=("SF Pro Text", 11),
            text_color=("gray60", "gray55")).pack(pady=(6, 2))

    # ── Settings Panel ───────────────────────────────────────
    def _build_settings_panel(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(2, 0))

        ctk.CTkLabel(header, text="⚙  Download Settings",
                     font=("SF Pro Display", 14, "bold"),
                     text_color=("gray25", "gray80")).pack(side="left")

        self.toggle_btn = ctk.CTkButton(
            header, text="▼ Show", font=("SF Pro Text", 12),
            width=70, height=26, corner_radius=13,
            fg_color="transparent", border_width=1,
            border_color=("gray70", "gray50"),
            text_color=("gray40", "gray65"),
            hover_color=("gray90", "gray30"),
            command=self._toggle_settings)
        self.toggle_btn.pack(side="right")

        self.settings_frame = ctk.CTkFrame(
            parent, fg_color=("gray93", "gray18"), corner_radius=12)
        self.settings_visible = False
        self._build_settings_content(parent)

    def _build_settings_content(self, parent):
        f = self.settings_frame

        def row(label, build_fn):
            r = ctk.CTkFrame(f, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(r, text=label, font=("SF Pro Text", 13),
                         text_color=("gray30", "gray75"),
                         width=130, anchor="w").pack(side="left")
            build_fn(r)

        self.quality_var = ctk.StringVar(value="1080P High Bitrate")
        row("Quality", lambda p: ctk.CTkOptionMenu(
            p, variable=self.quality_var,
            values=list(QUALITY_BBDOWN_MAP.keys()),
            width=215, font=("SF Pro Text", 13)).pack(side="left"))

        self.encoding_var = ctk.StringVar(value="avc")
        def _enc(p):
            ctk.CTkOptionMenu(p, variable=self.encoding_var,
                              values=["avc", "hevc", "av1"],
                              width=115, font=("SF Pro Text", 13)).pack(side="left")
            ctk.CTkLabel(p, text=" (Bilibili only)",
                         font=("SF Pro Text", 11),
                         text_color=("gray55", "gray55")).pack(side="left", padx=4)
        row("Encoding", _enc)

        self.api_mode_var = ctk.StringVar(value="TV API (No Watermark)")
        row("API Mode", lambda p: ctk.CTkOptionMenu(
            p, variable=self.api_mode_var,
            values=["TV API (No Watermark)", "APP API", "Web API (Default)"],
            width=215, font=("SF Pro Text", 13)).pack(side="left"))

        self.subtitle_var = ctk.BooleanVar(value=False)
        row("Subtitles", lambda p: ctk.CTkSwitch(
            p, text="Download subtitles",
            variable=self.subtitle_var,
            font=("SF Pro Text", 13),
            progress_color="#007AFF").pack(side="left"))

        self.multithread_var = ctk.BooleanVar(value=True)
        row("Multi-thread", lambda p: ctk.CTkSwitch(
            p, text="Multi-thread (faster)",
            variable=self.multithread_var,
            font=("SF Pro Text", 13),
            progress_color="#007AFF").pack(side="left"))

        self.capcut_uppercase_var = ctk.BooleanVar(value=False)
        row("CapCut SRT", lambda p: ctk.CTkSwitch(
            p, text="Auto-uppercase CapCut project",
            variable=self.capcut_uppercase_var,
            font=("SF Pro Text", 13),
            progress_color="#FF9500").pack(side="left"))

        def _manual_capcut(p):
            ctk.CTkButton(p, text="Select Project Manually...", width=175, height=26,
                          corner_radius=8, font=("SF Pro Text", 12),
                          fg_color="transparent", border_width=1,
                          border_color="#FF9500", text_color=("#FF9500", "#FFB347"),
                          command=self.select_capcut_manually).pack(side="left")
        row("CapCut Manual", _manual_capcut)

        def _folder(p):
            ctk.CTkEntry(p, textvariable=self.output_folder_var,
                         width=155, font=("SF Pro Text", 12)).pack(side="left", padx=(0, 6))
            ctk.CTkButton(p, text="Browse", width=68, height=26,
                          corner_radius=8, font=("SF Pro Text", 12),
                          command=self._browse_folder).pack(side="left")
        row("Output Folder", _folder)

        self.cookie_entry = ctk.CTkEntry(
            f, placeholder_text="Cookie (optional, for member-only content)...",
            width=410, height=32, font=("SF Pro Text", 12), corner_radius=8)
        self.cookie_entry.pack(padx=14, pady=(2, 10))

    def _toggle_settings(self):
        if self.settings_visible:
            self.settings_frame.pack_forget()
            self.toggle_btn.configure(text="▼ Show")
            self.settings_visible = False
        else:
            self.settings_frame.pack(fill="x", padx=20, pady=(6, 0))
            self.toggle_btn.configure(text="▲ Hide")
            self.settings_visible = True

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_folder_var.get())
        if folder:
            self.output_folder_var.set(folder)

    def _on_url_change(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            self.platform_label.configure(text="")
            return
        icons = {
            "bilibili": "📺  Bilibili → BBDown (no watermark)",
            "youtube":  "▶️  YouTube → yt-dlp",
            "tiktok":   "🎵  TikTok → yt-dlp",
            "other":    "🌐  Unknown → yt-dlp",
        }
        self.platform_label.configure(text=icons.get(detect_platform(url), ""))

    # ══════════════════════════════════════════════════════════
    #   VOCAL REMOVER TAB
    # ══════════════════════════════════════════════════════════
    def _build_vocal_tab(self, parent):
        # ── Drop zone / file picker ───────────────────────────
        ctk.CTkLabel(parent, text="Audio File  (MP3 / WAV / FLAC / M4A)",
                     font=("SF Pro Text", 13, "bold"),
                     text_color=("gray30", "gray75")).pack(anchor="w", padx=20, pady=(14, 4))

        drop_frame = ctk.CTkFrame(parent,
                                  fg_color=("gray90", "gray22"),
                                  corner_radius=12,
                                  border_width=2,
                                  border_color=("gray78", "gray35"))
        drop_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.vocal_file_label = ctk.CTkLabel(
            drop_frame,
            text="No file selected",
            font=("SF Pro Text", 13),
            text_color=("gray50", "gray60"))
        self.vocal_file_label.pack(side="left", padx=14, pady=12, expand=True)

        ctk.CTkButton(
            drop_frame, text="Browse…",
            font=("SF Pro Text", 13, "bold"), width=100, height=34,
            corner_radius=10, fg_color="#007AFF", hover_color="#005EC4",
            command=self._browse_audio_file).pack(side="right", padx=10, pady=8)

        self._vocal_file = None  # full path of selected file

        # ── Model selector ────────────────────────────────────
        model_row = ctk.CTkFrame(parent, fg_color="transparent")
        model_row.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(model_row, text="Model",
                     font=("SF Pro Text", 13, "bold"),
                     text_color=("gray30", "gray75"),
                     width=80, anchor="w").pack(side="left")

        self.vocal_model_var = ctk.StringVar(value=list(VOCAL_MODELS.keys())[0])
        ctk.CTkOptionMenu(
            model_row,
            variable=self.vocal_model_var,
            values=list(VOCAL_MODELS.keys()),
            width=380, height=36,
            font=("SF Pro Text", 13),
            corner_radius=10).pack(side="left", padx=8)

        ctk.CTkLabel(parent,
                     text="⚠  First run: model auto-downloads (~100-200 MB)",
                     font=("SF Pro Text", 11),
                     text_color=("gray55", "gray55")).pack(anchor="w", padx=20, pady=(0, 8))

        # ── Output folder ─────────────────────────────────────
        out_row = ctk.CTkFrame(parent, fg_color="transparent")
        out_row.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(out_row, text="Output",
                     font=("SF Pro Text", 13, "bold"),
                     text_color=("gray30", "gray75"),
                     width=80, anchor="w").pack(side="left")

        ctk.CTkEntry(out_row, textvariable=self.output_folder_var,
                     width=300, font=("SF Pro Text", 12)).pack(side="left", padx=(8, 6))

        ctk.CTkButton(out_row, text="Browse", width=80, height=32,
                      corner_radius=10, font=("SF Pro Text", 12),
                      command=self._browse_folder).pack(side="left")

        # ── Convert to MP3 option ─────────────────────────────
        self.vocal_mp3_var = ctk.BooleanVar(value=True)
        mp3_row = ctk.CTkFrame(parent, fg_color="transparent")
        mp3_row.pack(fill="x", padx=20, pady=(4, 2))
        ctk.CTkLabel(mp3_row, text="",  width=80).pack(side="left")
        ctk.CTkSwitch(mp3_row, text="Convert output to MP3  (via ffmpeg)",
                      variable=self.vocal_mp3_var,
                      font=("SF Pro Text", 13),
                      progress_color="#34C759").pack(side="left", padx=8)

        # ── Progress + status ─────────────────────────────────
        self.vocal_progress = ctk.CTkProgressBar(
            parent, width=520, height=5, corner_radius=3,
            progress_color="#FF375F", mode="indeterminate")
        self.vocal_progress.pack(pady=(14, 4))
        self.vocal_progress.pack_forget()

        self.vocal_status_label = ctk.CTkLabel(
            parent, text="Ready ✓",
            font=("SF Pro Text", 12),
            text_color=("gray45", "gray60"))
        self.vocal_status_label.pack(pady=(0, 10))

        # ── Main action button ────────────────────────────────
        self.vocal_btn = ctk.CTkButton(
            parent, text="🎤  Remove Vocals",
            font=("SF Pro Text", 16, "bold"),
            width=220, height=50, corner_radius=25,
            fg_color="#FF375F", hover_color="#C62348",
            command=self.start_vocal_removal)
        self.vocal_btn.pack(pady=(4, 14))

        # ── Result display ────────────────────────────────────
        ctk.CTkFrame(parent, height=1, width=520,
                     fg_color=("gray82", "gray32")).pack(pady=(0, 10))

        ctk.CTkLabel(parent, text="Output Files",
                     font=("SF Pro Text", 12, "bold"),
                     text_color=("gray40", "gray65")).pack(anchor="w", padx=20)

        self.vocal_result_box = ctk.CTkTextbox(
            parent, width=520, height=70, corner_radius=10,
            font=("SF Mono", 12), fg_color=("gray93", "gray18"),
            text_color=("gray20", "gray85"),
            state="disabled")
        self.vocal_result_box.pack(padx=20, pady=(4, 10))

        # Apple Silicon badge
        if _is_apple_silicon():
            ctk.CTkLabel(
                parent,
                text="🍎  Apple Silicon detected — CoreML acceleration active",
                font=("SF Pro Text", 11),
                text_color=("#34C759", "#30D158")).pack(pady=(0, 6))

    def _browse_audio_file(self):
        path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("All Files", "*.*"),
            ]
        )
        if not path:
            return
        self._vocal_file = path
        name = os.path.basename(path)
        display = name if len(name) <= 52 else "…" + name[-50:]
        self.vocal_file_label.configure(
            text=f"📄  {display}",
            text_color=("gray15", "gray90"))

    # ── Vocal Removal Entry Point ─────────────────────────────
    def start_vocal_removal(self):
        if self._vocal_busy:
            return
        if not self._vocal_file or not os.path.isfile(self._vocal_file):
            self._shake_vocal()
            return
        model_label = self.vocal_model_var.get()
        model_name = VOCAL_MODELS.get(model_label, "UVR-MDX-NET-Inst_HQ_4.onnx")
        out_dir = self.output_folder_var.get()
        convert_mp3 = self.vocal_mp3_var.get()

        self._set_vocal_busy(True)
        self._set_vocal_status("🔍  Loading model…", ("gray50", "gray60"))
        self._clear_result_box()

        threading.Thread(
            target=self._vocal_worker,
            args=(self._vocal_file, model_name, out_dir, convert_mp3),
            daemon=True
        ).start()

    def _vocal_worker(self, input_path, model_name, out_dir, convert_mp3):
        try:
            from audio_separator.separator import Separator

            # Build separator kwargs
            # Note: Apple Silicon (MPS) acceleration is handled automatically
            # by audio-separator internally — no need to pass it explicitly.
            sep_kwargs = dict(output_dir=out_dir, output_format="wav")

            self._ui(lambda: self._set_vocal_status("⚙  Initialising separator…"))

            sep = Separator(**sep_kwargs)

            self._ui(lambda: self._set_vocal_status(
                f"⬇  Loading model (may download on first use)…"))
            sep.load_model(model_filename=model_name)

            self._ui(lambda: self._set_vocal_status("🎵  Separating audio…  (this may take a minute)"))
            output_files = sep.separate(input_path)

            if not output_files:
                raise RuntimeError("Separator returned no output files.")

            # Separator may return bare filenames or full paths — normalize to full paths
            resolved = []
            for f in output_files:
                if os.path.isabs(f) and os.path.exists(f):
                    resolved.append(f)
                else:
                    full = os.path.join(out_dir, os.path.basename(f))
                    resolved.append(full)
            output_files = resolved

            final_files = output_files

            # Optional MP3 conversion
            if convert_mp3 and shutil.which("ffmpeg"):
                self._ui(lambda: self._set_vocal_status("🔄  Converting to MP3…"))
                converted = []
                for wav_path in output_files:
                    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"
                    cmd = ["ffmpeg", "-y", "-i", wav_path, "-q:a", "2", mp3_path]
                    result = subprocess.run(cmd, capture_output=True)
                    if result.returncode == 0 and os.path.exists(mp3_path):
                        if os.path.exists(wav_path):
                            os.remove(wav_path)
                        converted.append(mp3_path)
                    else:
                        converted.append(wav_path)  # keep wav if conversion fails
                final_files = converted

            # Build result display
            names = [os.path.basename(f) for f in final_files]
            result_text = "\n".join(names)
            self._ui(lambda: self._on_vocal_success(result_text, out_dir))

        except ImportError:
            self._ui(lambda: self._on_vocal_error(
                "audio-separator not installed.\n"
                "Run: pip install 'audio-separator[cpu]' in the venv."))
        except Exception as e:
            err = str(e)
            self._ui(lambda: self._on_vocal_error(f"Error: {err}"))

    # ── Vocal tab helpers ─────────────────────────────────────
    def _set_vocal_busy(self, busy: bool):
        self._vocal_busy = busy
        if busy:
            self.vocal_btn.configure(state="disabled")
            self.vocal_progress.pack(pady=(14, 4))
            self.vocal_progress.start()
        else:
            self.vocal_progress.stop()
            self.vocal_progress.pack_forget()
            self.vocal_btn.configure(state="normal")

    def _set_vocal_status(self, text, color=("gray45", "gray60")):
        self.vocal_status_label.configure(text=text, text_color=color)

    def _clear_result_box(self):
        self.vocal_result_box.configure(state="normal")
        self.vocal_result_box.delete("1.0", "end")
        self.vocal_result_box.configure(state="disabled")

    def _on_vocal_success(self, file_list_text, out_dir):
        self._set_vocal_busy(False)
        self._set_vocal_status("✅  Done! Files saved.", "#34C759")
        self.vocal_result_box.configure(state="normal")
        self.vocal_result_box.delete("1.0", "end")
        self.vocal_result_box.insert("end", file_list_text)
        self.vocal_result_box.configure(state="disabled")
        folder_name = os.path.basename(out_dir)
        messagebox.showinfo(
            "Done ✓",
            f"Vocal removal complete!\n\n{file_list_text}\n\n→ Saved to: {out_dir}")

    def _on_vocal_error(self, msg):
        self._set_vocal_busy(False)
        self._set_vocal_status(msg[:80], "#FF3B30")
        messagebox.showerror("Failed", msg)

    def _shake_vocal(self):
        self._set_vocal_status("Please select an audio file first!", "#FF3B30")
        self.after(2000, lambda: self._set_vocal_status("Ready ✓", ("gray45", "gray60")))

    # ── Tool Check ───────────────────────────────────────────
    def _check_tools(self):
        warnings = []
        if not os.path.exists(BBDOWN_PATH):
            warnings.append("BBDown not found")
        elif not os.access(BBDOWN_PATH, os.X_OK):
            os.chmod(BBDOWN_PATH, 0o755)
        if not shutil.which("ffmpeg"):
            warnings.append("ffmpeg not found")
        if not shutil.which("yt-dlp"):
            warnings.append("yt-dlp not found")
        if warnings:
            self._set_status("⚠ " + " | ".join(warnings), "orange")
        else:
            self._set_status("✓ All tools ready", "#34C759")

    # ── Thread-safe UI helpers ───────────────────────────────
    def _set_status(self, text, color=("gray45", "gray60")):
        self.status_label.configure(text=text, text_color=color)

    def _ui(self, func):
        self.after(0, func)

    # ── Busy state (Download tab) ────────────────────────────
    def _set_busy(self, busy: bool):
        if busy:
            self._busy = True
            self.download_btn.configure(state="disabled")
            self.thumb_btn.configure(state="disabled")
            self.capcut_btn.configure(state="disabled")
            self.url_entry.configure(state="disabled")
            self.progress.pack(pady=6)
            self.progress.start()
        else:
            self._busy = False
            self.progress.stop()
            self.progress.pack_forget()
            self.download_btn.configure(state="normal")
            self.thumb_btn.configure(state="normal")
            self.capcut_btn.configure(state="normal")
            self.url_entry.configure(state="normal")

    # ── Download entry points ────────────────────────────────
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self._shake()
            return
        self._set_busy(True)
        self._ui(lambda: self._set_status("Starting download..."))
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def start_thumbnail(self):
        url = self.url_entry.get().strip()
        if not url:
            self._shake()
            return
        self._set_busy(True)
        self._ui(lambda: self._set_status("Fetching thumbnail..."))
        threading.Thread(target=self._thumb_worker, args=(url,), daemon=True).start()

    def start_capcut_extraction(self):
        recent = capcut_utils.get_recent_projects()
        if not recent:
            self._set_status("No CapCut projects found", "#FF3B30")
            messagebox.showwarning("Not Found",
                "No CapCut projects found in the default directory.\n"
                "Please select manually in Settings.")
            return
        latest = recent[0]
        name = latest.get('draft_name', 'Unknown')
        json_path = latest.get('draft_json_file')
        if not json_path or not os.path.exists(json_path):
            self._set_status("Project file not found", "#FF3B30")
            return
        self._set_busy(True)
        self._ui(lambda: self._set_status(f"Extracting: {name}..."))
        threading.Thread(target=self._capcut_worker, args=(json_path,), daemon=True).start()

    def select_capcut_manually(self):
        default_path = capcut_utils.get_default_capcut_path()
        file_path = filedialog.askopenfilename(
            title="Select CapCut project file (draft_info.json)",
            initialdir=default_path,
            filetypes=[("CapCut Draft Info", "draft_info.json"),
                       ("CapCut Draft Content", "draft_content.json"),
                       ("JSON Files", "*.json")])
        if not file_path:
            return
        self._set_busy(True)
        name = os.path.basename(os.path.dirname(file_path))
        self._ui(lambda: self._set_status(f"Extracting: {name}..."))
        threading.Thread(target=self._capcut_worker, args=(file_path,), daemon=True).start()

    # ── Background workers ───────────────────────────────────
    def _download_worker(self, url):
        try:
            platform = detect_platform(url)
            out_dir = self.output_folder_var.get()
            bv = re.search(r'BV[a-zA-Z0-9]+', url)
            vid_id = bv.group(0) if bv else hashlib.md5(url.encode()).hexdigest()[:8]
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            folder = os.path.join(out_dir, f"{ts}_{platform}_{sanitize(vid_id, 20)}")
            os.makedirs(folder, exist_ok=True)
            if platform == "bilibili":
                self._run_bilibili(url, folder)
            else:
                self._run_ytdlp(url, folder)
        except Exception as e:
            self._ui(lambda: self._on_error(f"Error: {e}"))

    def _thumb_worker(self, url):
        try:
            plat = detect_platform(url)
            out_dir = self.output_folder_var.get()
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            folder = os.path.join(out_dir, f"{ts}_{plat}_thumb")
            os.makedirs(folder, exist_ok=True)
            if plat == "bilibili":
                cmd = [BBDOWN_PATH, url, "--cover-only", "--work-dir", folder]
            else:
                tpl = os.path.join(folder, "%(title)s.%(ext)s")
                cmd = ["yt-dlp", "--write-thumbnail", "--skip-download",
                       "--convert-thumbnails", "jpg", "--no-playlist", "-o", tpl, url]
            ok, err = self._run_cmd(cmd)
            if ok:
                self._ui(lambda: self._on_success(
                    f"✓ Thumbnail saved → {os.path.basename(folder)}"))
            else:
                self._ui(lambda: self._on_error(f"Failed to get thumbnail.\n{err}"))
        except Exception as e:
            self._ui(lambda: self._on_error(f"Error: {e}"))

    def _capcut_worker(self, json_path):
        try:
            out_dir = self.output_folder_var.get()
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
            project_name = os.path.basename(os.path.dirname(json_path))
            filename = f"CapCut_{project_name}_{ts}.srt"
            output_path = os.path.join(out_dir, filename)
            up_msg = ""
            if self.capcut_uppercase_var.get():
                ok_up, count = capcut_utils.uppercase_draft(json_path)
                if ok_up and count > 0:
                    up_msg = f" (Uppercased {count} captions)"
                elif not ok_up:
                    self._ui(lambda: self._set_status(f"Uppercase failed: {count}", "orange"))
            success, result = capcut_utils.extract_srt(json_path, output_path)
            if success:
                self._ui(lambda: self._on_success(
                    f"✓ Extracted {result} subtitles!{up_msg} \n→ {filename}"))
            else:
                self._ui(lambda: self._on_error(f"Extraction failed: {result}"))
        except Exception as e:
            self._ui(lambda: self._on_error(f"Error: {e}"))

    # ── Bilibili via BBDown ──────────────────────────────────
    def _run_bilibili(self, url, folder):
        quality_en = self.quality_var.get()
        quality_cn = QUALITY_BBDOWN_MAP.get(quality_en, "1080P 高码率")
        encoding   = self.encoding_var.get()
        cookie     = self.cookie_entry.get().strip()
        use_mt     = self.multithread_var.get()
        skip_sub   = not self.subtitle_var.get()
        cmd = [BBDOWN_PATH, url, "-q", quality_cn, "-e", encoding, "--work-dir", folder]
        api_mode = self.api_mode_var.get()
        if "TV API" in api_mode:
            cmd.append("-tv")
        elif "APP API" in api_mode:
            cmd.append("-app")
        if use_mt:
            cmd.append("-mt")
        if skip_sub:
            cmd.append("--skip-subtitle")
        if cookie:
            cmd += ["-c", cookie]
        self._ui(lambda: self._set_status(f"BBDown: {quality_en} / {encoding.upper()}..."))
        ok, err = self._run_cmd(cmd, self._parse_bbdown_line)
        folder_name = os.path.basename(folder)
        if ok:
            self._ui(lambda: self._on_success(f"✓ Saved → {folder_name}"))
        else:
            self._ui(lambda: self._on_error(f"BBDown failed.\n{err}"))

    # ── Other platforms via yt-dlp ───────────────────────────
    def _run_ytdlp(self, url, folder):
        quality = self.quality_var.get()
        fmt = QUALITY_YTDLP_MAP.get(quality, "bestvideo+bestaudio/best")
        tpl = os.path.join(folder, "%(title)s.%(ext)s")
        cmd = ["yt-dlp", "-f", fmt, "--merge-output-format", "mp4",
               "--no-playlist", "-o", tpl, url]
        if self.subtitle_var.get():
            cmd += ["--write-subs", "--sub-langs", "zh-Hans,vi,en"]
        self._ui(lambda: self._set_status(f"yt-dlp: downloading ({quality})..."))
        ok, err = self._run_cmd(cmd, self._parse_ytdlp_line)
        folder_name = os.path.basename(folder)
        if ok:
            self._ui(lambda: self._on_success(f"✓ Saved → {folder_name}"))
        else:
            self._ui(lambda: self._on_error(f"yt-dlp failed.\n{err}"))

    # ── Process runner ───────────────────────────────────────
    def _run_cmd(self, cmd, line_parser=None):
        import pty, select
        master_fd, slave_fd = pty.openpty()
        process = subprocess.Popen(cmd, stdout=slave_fd, stderr=slave_fd, close_fds=True)
        os.close(slave_fd)
        last_err = ""
        buf = b""
        while process.poll() is None:
            r, _, _ = select.select([master_fd], [], [], 0.1)
            if not r:
                continue
            try:
                chunk = os.read(master_fd, 512)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            parts = re.split(rb'[\r\n]', buf)
            buf = parts[-1]
            for raw in parts[:-1]:
                try:
                    line = raw.decode("utf-8", errors="replace").strip()
                except Exception:
                    continue
                if not line:
                    continue
                if "Error" in line or "error" in line or "错误" in line or "failed" in line:
                    if len(line) < 100:
                        last_err = line
                if line_parser:
                    line_parser(line)
        if buf:
            try:
                line = buf.decode("utf-8", errors="replace").strip()
                if line and line_parser:
                    line_parser(line)
            except Exception:
                pass
        process.wait()
        os.close(master_fd)
        return (process.returncode == 0), last_err

    # ── Line parsers ─────────────────────────────────────────
    def _parse_bbdown_line(self, line: str):
        if "%" in line and ("MB/s" in line or "KB/s" in line):
            pct_match = re.search(r'(\d+)%', line)
            spd_match = re.search(r'[\d.]+\s*[MK]B/s', line)
            if pct_match:
                pct = pct_match.group(0)
                spd = spd_match.group(0) if spd_match else ""
                self._ui(lambda p=pct, s=spd: self._set_status(f"⬇  {p}  {s}".strip()))
            return
        if "视频标题" in line:
            title = line.split(":")[-1].strip() if ":" in line else ""
            if title:
                self._ui(lambda t=title: self._set_status(f"📺  {t[:55]}"))
            return
        for zh, vi in BBDOWN_STATUS_MAP:
            if zh in line:
                if vi:
                    self._ui(lambda m=vi: self._set_status(m))
                return
        if re.search(r'\[\d+[KP]', line) and "kbps" in line:
            self._ui(lambda l=line: self._set_status(f"ℹ  {l[:70]}"))

    def _parse_ytdlp_line(self, line: str):
        if "[download]" in line and "%" in line:
            short = line.split("ETA")[0].replace("[download]", "").strip()
            self._ui(lambda s=short: self._set_status(f"⬇  {s}"))
        elif any(k in line for k in ["Merging", "[ffmpeg]", "Destination"]):
            self._ui(lambda l=line: self._set_status(f"🔀  {l[:70]}"))

    # ── Success / Error (Download tab) ──────────────────────
    def _on_success(self, msg):
        self._set_busy(False)
        self._set_status(msg, "#28CC2D")
        messagebox.showinfo("Done ✓", msg)

    def _on_error(self, msg):
        self._set_busy(False)
        self._set_status(msg[:80], "#FF3B30")
        messagebox.showerror("Failed", msg)

    def _shake(self):
        orig = self.url_entry.cget("border_color")
        self.url_entry.configure(border_color="#FF3B30")
        self.after(500, lambda: self.url_entry.configure(border_color=orig))
        self._set_status("Please enter a URL", "#FF3B30")


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()

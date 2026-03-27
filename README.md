# Video Downloader Pro

A powerful, modern desktop application with a clean UI built in Python using `customtkinter`. This tool allows you to seamlessly download videos from various platforms like Bilibili, YouTube, TikTok, and more. It also features a built-in utility to extract subtitle (SRT) files directly from your CapCut project drafts.

## 🌟 Features

*   **Bilibili Downloads (No Watermark):** Leverages BBDown to download high-quality, watermark-free Bilibili videos. Supports various qualities up to 8K, custom encodings (AVC, HEVC, AV1), and different API modes (TV, App, Web).
*   **YouTube, TikTok & Others:** Uses `yt-dlp` to download from almost any other platform. 
*   **Thumbnail Extraction:** Quickly download just the video thumbnail without downloading the entire video.
*   **CapCut SRT Extraction:** Automatically detects your most recently modified CapCut project and extracts its captions into a standard `.srt` subtitle file.
*   **Auto-Uppercase Subtitles:** Includes an option to automatically convert all captions in your CapCut draft to uppercase.
*   **Modern UI:** A beautiful Apple-style design philosophy using system presence and blue color theme.
*   **Advanced Settings:** 
    *   Choose download quality.
    *   Toggle multi-threading for faster downloads.
    *   Optionally download subtitles along with videos.
    *   Custom cookie support for member-only content.
    *   Custom output folder selection.

## ⚙️ Requirements

Ensure you have the following installed on your system:
*   Python 3.x
*   `customtkinter`, `tkinter`
*   `ffmpeg` (Must be installed and added to your system PATH)
*   `yt-dlp` (Must be installed and added to your system PATH)

## 🚀 How to Use

1.  **Launch the App:** Run the `video_downloader_gui.py` script.
2.  **Paste URL:** Paste the URL of the video you want to download (Bilibili, YouTube, TikTok, etc.) into the main input field.
3.  **Adjust Settings (Optional):** Click "Show settings" to tweak quality, select the output folder, toggle subtitles, or add cookies.
4.  **Download Actions:**
    *   **Download Video:** Click to start downloading the video and audio to your selected output folder.
    *   **Get Thumbnail:** Click to fetch and save only the video's thumbnail.
5.  **CapCut SRT Extraction:** 
    *   Click "Extract CapCut SRT" to automatically process your most recently edited CapCut project and generate an SRT file in your output directory.
    *   You can also manually select a specific CapCut `draft_info.json` file via the Settings panel.

## 🙏 Credits

This project integrates and builds upon the excellent work of the following open-source projects:

*   **BBDown**: Used for high-quality, watermark-free Bilibili video downloading. 
    Source: [https://github.com/nilaoda/BBDown](https://github.com/nilaoda/BBDown)
*   **CapCut SRT Export Logic**: Inspired by and ported from the CapCut SRT export utility.
    Source: [https://github.com/vogelcodes/capcut-srt-export](https://github.com/vogelcodes/capcut-srt-export)

---
*Built with ❤️ for content creators and video enthusiasts.*

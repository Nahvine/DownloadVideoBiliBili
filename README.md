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

### 📱 Common
*   **Python 3.x**: [Download here](https://www.python.org/downloads/)
*   **customtkinter**: `pip install customtkinter`
*   **ffmpeg**: Must be installed and added to your system PATH.
*   **yt-dlp**: `pip install yt-dlp` (Must be added to your system PATH).

### 🖥️ Platform Specific
*   **macOS**: The project includes a `BBDown` binary for Bilibili downloads.
*   **Windows**: The project includes `BBDown.exe` for Bilibili downloads. 
    *   *Note: Ensure you have the [.NET Runtime](https://dotnet.microsoft.com/download/dotnet) installed as required by BBDown.*

## 🚀 How to Use

### 🪟 Windows
1.  Open PowerShell or Command Prompt in the project folder.
2.  Run: `python video_downloader_gui.py`

### 🍎 macOS
1.  Open Terminal in the project folder.
2.  Run: `python3 video_downloader_gui.py`
3.  *Note: You may need to grant execution permission to the command: `chmod +x BBDown`*

### 📥 General Usage
1.  **Paste URL:** Paste the URL of the video (Bilibili, YouTube, TikTok, etc.).
2.  **Adjust Settings (Optional):** Click "Show settings" to tweak quality, output folder, or add cookies.
3.  **Download Actions:**
    *   **Download Video:** Start downloading everything to your selected folder.
    *   **Get Thumbnail:** Fetch and save only the video's thumbnail.
4.  **CapCut SRT Extraction:** 
    *   Click "Extract CapCut SRT" to process your latest CapCut project.
    *   Manual selection is available in the Settings panel.

## 🙏 Credits

This project integrates and builds upon the excellent work of the following open-source projects:

*   **BBDown**: High-quality Bilibili video downloader. 
    [https://github.com/nilaoda/BBDown](https://github.com/nilaoda/BBDown)
*   **yt-dlp**: Universal video downloader.
    [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
*   **CapCut SRT Export Logic**: Inspired by the work at:
    [https://github.com/vogelcodes/capcut-srt-export](https://github.com/vogelcodes/capcut-srt-export)

---
*Built with ❤️ for content creators and video enthusiasts.*

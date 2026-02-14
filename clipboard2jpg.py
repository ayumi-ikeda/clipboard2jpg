#!/usr/bin/env python3
import sys
import argparse
import subprocess
import shutil
import datetime

import io
import os
import base64
import platform

VERSION = "0.1.1"

def get_unique_filename():
    """ユニークなファイル名を生成 (タイムスタンプベース)"""
    now = datetime.datetime.now()
    # Format: clipboard2jpg_YYYYMMDD_HHMMSS_microseconds.jpg
    return f"clipboard2jpg_{now.strftime('%Y%m%d_%H%M%S_%f')}.jpg"

def detect_platform():
    """環境を判別する (Darwin, WSL2, Wayland, X11)"""
    sys_name = platform.system()
    if sys_name == "Darwin":
        return "macOS"
    if sys_name == "Linux":
        # WSL2 Check (Linux + microsoft)
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return "WSL2"
        except:
            pass
        # Wayland Check (Linux + wayland)
        if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland":
            return "Wayland"
        # X11 Check (Linux + x11)
        return "X11"
    return "Unknown"

def grab_from_wayland():
    """Wayland環境 (wl-paste) から画像を取得"""
    from PIL import Image
    if not shutil.which("wl-paste"): return None
    try:
        result = subprocess.run(["wl-paste", "--list-types"], capture_output=True, text=True, timeout=2)
        if result.returncode != 0: return None
        targets = result.stdout.splitlines()
        mime = next((t for t in targets if t.startswith("image/")), None)
        if mime:
            data = subprocess.check_output(["wl-paste", "--type", mime], timeout=5)
            return Image.open(io.BytesIO(data))
    except:
        pass
    return None

def grab_from_x11():
    """X11環境 (xclip) から画像を取得"""
    from PIL import Image
    if not shutil.which("xclip"): return None
    try:
        result = subprocess.run(["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"], capture_output=True, text=True, timeout=2)
        if result.returncode != 0: return None
        targets = result.stdout.splitlines()
        mime = next((t for t in targets if t.startswith("image/") or t in ["PIXMAP", "BMP"]), None)
        if mime:
            data = subprocess.check_output(["xclip", "-selection", "clipboard", "-t", mime, "-o"], timeout=5)
            return Image.open(io.BytesIO(data))
    except:
        pass
    return None

def grab_from_wsl():
    """WSL2環境 (powershell.exe) から画像を取得"""
    from PIL import Image
    if not shutil.which("powershell.exe"): return None
    
    # Windows側のPowerShellを利用してクリップボード画像を取得しBase64で受け渡し
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$img = [Windows.Forms.Clipboard]::GetImage(); "
        "if ($img) { "
        "  $ms = New-Object System.IO.MemoryStream; "
        "  $img.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png); "
        "  [System.Convert]::ToBase64String($ms.ToArray()); "
        "}"
    )
    try:
        res = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], 
                             capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return Image.open(io.BytesIO(base64.b64decode(res.stdout)))
    except:
        pass
    return None

def is_clipboard_empty(env):
    """クリップボードが空かどうかを環境別にチェック"""
    if env == "Wayland":
        if not shutil.which("wl-paste"): return True
        return subprocess.run(["wl-paste", "--list-types"], capture_output=True).returncode != 0
    if env == "X11":
        if not shutil.which("xclip"): return True
        return subprocess.run(["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"], capture_output=True).returncode != 0
    if env == "WSL2":
        if not shutil.which("powershell.exe"): return True
        res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard | Out-Null"], capture_output=True)
        return res.returncode != 0
    if env == "macOS":
        if not shutil.which("pbpaste"): return True
        # テキストか画像情報があるか確認
        has_text = subprocess.run(["pbpaste"], capture_output=True).stdout.strip() != b""
        has_other = subprocess.run(["osascript", "-e", "clipboard info"], capture_output=True).returncode == 0
        return not (has_text or has_other)
    return True

def main():
    parser = argparse.ArgumentParser(description="Save clipboard image to JPG file.")
    parser.add_argument("-o", "--output", help="Output file name")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()

    # PIL Check
    try:
        from PIL import ImageGrab, Image
    except ImportError:
        print("error: Pillow library not found. Please install it (e.g., `pip install Pillow`).", file=sys.stderr)
        sys.exit(1)

    env = detect_platform()

    try:
        # 1. ImageGrab (Native macOS/Windows, X11 fallback) を試す
        img = None
        try:
            img = ImageGrab.grabclipboard()
        except:
            pass

        # 2. 個別環境のツールを試す
        if not isinstance(img, Image.Image):
            if env == "Wayland":
                img = grab_from_wayland()
            elif env == "WSL2":
                img = grab_from_wsl()
            elif env == "X11":
                img = grab_from_x11()

        if isinstance(img, Image.Image):
            # 画像取得成功
            pass
        else:
            # エラー判定
            if is_clipboard_empty(env):
                print("error : empty", file=sys.stderr)
            else:
                print("error: no image", file=sys.stderr)
            sys.exit(1)

        # ファイル名の決定
        if args.output:
            save_path = args.output
            if not save_path.lower().endswith(('.jpg', '.jpeg')):
                save_path += ".jpg"
        else:
            save_path = get_unique_filename()

        try:
            # Ensure RGB mode (JPG does not support RGBA/P)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(save_path, "JPEG")
            sys.exit(0)
        except Exception as e:
            print(f"error: failed to save file: {e}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

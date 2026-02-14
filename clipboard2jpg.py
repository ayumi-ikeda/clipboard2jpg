#!/usr/bin/env python3
import sys
import argparse
import subprocess
import shutil
import datetime

VERSION = "0.0.0"

def get_unique_filename():
    """Generate a unique filename based on the current timestamp."""
    now = datetime.datetime.now()
    # Format: clipboard2jpg_YYYYMMDD_HHMMSS_microseconds.jpg
    return f"clipboard2jpg_{now.strftime('%Y%m%d_%H%M%S_%f')}.jpg"

def main():
    parser = argparse.ArgumentParser(description="Save clipboard image to JPG file.")
    parser.add_argument("-o", "--output", help="Output file name")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()

    # Check for Pillow library
    try:
        from PIL import ImageGrab, Image
    except ImportError:
        print("error: Pillow library not found. Please install it (e.g., `pip install Pillow`).", file=sys.stderr)
        sys.exit(1)

    # Check for xclip on Linux
    if sys.platform.startswith("linux") and not shutil.which("xclip"):
        print("error: 'xclip' not found. Please install xclip (e.g., `sudo apt install xclip`).", file=sys.stderr)
        sys.exit(1)

    try:
        # Grab image from clipboard
        img = ImageGrab.grabclipboard()

        if isinstance(img, Image.Image):
            # Image found
            pass
        else:
            # Need to distinguish between empty clipboard and non-image content
            if sys.platform.startswith("linux"):
                try:
                    # Check available targets using xclip
                    # -t TARGETS is fast and metadata-only
                    result = subprocess.run(
                        ['xclip', '-selection', 'clipboard', '-t', 'TARGETS', '-o'],
                        capture_output=True, text=True, timeout=2, check=False
                    )
                    
                    # If return code is non-zero or output is empty, clipboard is likely empty
                    if result.returncode != 0 or not result.stdout.strip():
                        print("error : empty", file=sys.stderr)
                        sys.exit(1)
                    
                    # If targets exist but Pillow returned None, it means no supported image data
                    print("error: no image", file=sys.stderr)
                    sys.exit(1)

                except Exception:
                    # If xclip fails unexpectedly or times out, assume empty or inaccessible
                    print("error : empty", file=sys.stderr)
                    sys.exit(1)
            else:
                # Non-linux fallback (e.g. Mac/Windows handles grabclipboard differently)
                # But request is for generic/linux via xclip context. 
                # Pillow returns None if empty or non-image usually.
                print("error: no image", file=sys.stderr)
                sys.exit(1)

        # Determine output filename
        if args.output:
            save_path = args.output
            # Append .jpg extension if missing (case-insensitive check)
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

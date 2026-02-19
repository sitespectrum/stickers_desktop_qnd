import platform
import subprocess
import os

from PIL import Image
import io

def copy_image(path):
    system = platform.system()

    img = Image.open(path)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    if system == "Windows":
        import win32clipboard as clp

        file_path = path

        clp.OpenClipboard()
        clp.EmptyClipboard()

        # This works for Discord, but not for Paint:
        wide_path = os.path.abspath(file_path).encode('utf-16-le') + b'\0'
        clp.SetClipboardData(clp.RegisterClipboardFormat('FileNameW'), wide_path)

        # This works for Paint, but not for Discord:
        file = open(file_path, 'rb')
        clp.SetClipboardData(clp.RegisterClipboardFormat('image/png'), file.read())

        clp.CloseClipboard()

    elif system == "Darwin":
        # import AppKit
        # nsdata = AppKit.NSData.dataWithBytes_length_(png_bytes, len(png_bytes))
        # image = AppKit.NSImage.alloc().initWithData_(nsdata)
        #
        # pb = AppKit.NSPasteboard.generalPasteboard()
        # pb.clearContents()
        # pb.writeObjects_([image])
        pass

    else:
        try:
            p = subprocess.Popen(["wl-copy", "--type", "image/png"], stdin=subprocess.PIPE)
            p.communicate(png_bytes)
            if p.returncode == 0:
                return
        except FileNotFoundError:
            pass

        subprocess.Popen([
            "xclip",
            "-selection", "clipboard",
            "-t", "image/png",
            "-i"
        ], stdin=subprocess.PIPE).communicate(png_bytes)

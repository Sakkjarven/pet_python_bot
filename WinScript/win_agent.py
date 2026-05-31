import os
import urllib.parse
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

class WindowsAgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        # Обработка команды SAY
        if parsed_url.path == '/say':
            text = params.get('text', [''])[0]
            print(f"Requested to say: {text}")
            
            ps_cmd = f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak('{text}')"
            subprocess.run(["powershell.exe", "-Command", ps_cmd])
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Status: Spoken")
            
        elif parsed_url.path == '/scr':
            print("Screenshot requested")
            img_path = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), 'docker_scr.png')
            
            if os.path.exists(img_path):
                os.remove(img_path)
                
            ps_cmd = (
                "[Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null; "
                "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
                "$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; "
                "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
                "$graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size); "
                f"$bmp.Save('{img_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
                "$graphics.Dispose(); $bmp.Dispose();"
            )
            subprocess.run(["powershell.exe", "-Command", ps_cmd])
            
            if os.path.exists(img_path):
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open(img_path, 'rb') as f:
                    self.wfile.write(f.read())
                os.remove(img_path)
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error: Screen failed")
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 5000), WindowsAgentHandler)
    print("Agent running at http://127.0.0.1:5000")
    server.serve_forever()

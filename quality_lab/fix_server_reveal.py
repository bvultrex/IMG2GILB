from pathlib import Path

p = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\server.py")
# always restore from clean backup first
bak = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\server.py.bak_interim")
text = bak.read_text(encoding="utf-8")

if "import subprocess" not in text:
    text = text.replace(
        "import base64,io,json,math,mimetypes,os,re,secrets,sys,threading,time,uuid,zipfile",
        "import base64,io,json,math,mimetypes,os,re,secrets,subprocess,sys,threading,time,uuid,zipfile",
    )

marker = "if path=='/api/config':"
if "/api/open_jobs" not in text:
    add = (
        "if path=='/api/open_jobs':\n"
        "   subprocess.Popen(['explorer',str(JOBS)],creationflags=subprocess.CREATE_NO_WINDOW);"
        "return self.response(200,{'ok':True,'path':str(JOBS)})\n"
        "  "
    )
    text = text.replace(marker, add + marker)

start = text.find("m=re.fullmatch(r'/api/jobs/([a-f0-9]{32})/(cancel|retry)',path)")
if start < 0:
    raise SystemExit("start missing")
snap = "return self.response(202,ACTIVE.snapshot())"
first = text.find(snap, start)
second = text.find(snap, first + 1)
if second < 0:
    raise SystemExit("second snap missing")
end = second + len(snap)
block = text[start:end]
block = block.replace("(cancel|retry)", "(cancel|retry|reveal)", 1)
# insert reveal after cancel's snapshot return (first snap)
idx = block.find(snap)
idx_end = idx + len(snap)
reveal = (
    "\n"
    "     if action=='reveal':\n"
    "      if not (job/'state.json').is_file():return self.response(404,{'error':'Projekt nicht gefunden'})\n"
    "      focus=job/'output.glb'\n"
    "      if focus.is_file():\n"
    "       subprocess.Popen(['explorer','/select,',str(focus)],creationflags=subprocess.CREATE_NO_WINDOW)\n"
    "      else:\n"
    "       subprocess.Popen(['explorer',str(job)],creationflags=subprocess.CREATE_NO_WINDOW)\n"
    "      return self.response(200,{'ok':True,'path':str(job)})"
)
block = block[:idx_end] + reveal + block[idx_end:]
text = text[:start] + block + text[end:]
p.write_text(text, encoding="utf-8")
compile(text, str(p), "exec")
assert text.find("action=='reveal'") < text.find("if __name__")
assert text.count("action=='reveal'") == 1
print("FIXED OK")
print(text[text.find("action=='reveal'") - 120 : text.find("action=='reveal'") + 280])

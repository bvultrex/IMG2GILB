from pathlib import Path

p = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\server.py")
text = p.read_text(encoding="utf-8")
backup = p.with_suffix(".py.bak_interim")
if not backup.exists():
    backup.write_text(text, encoding="utf-8")

if "import subprocess" not in text:
    text = text.replace(
        "import base64,io,json,math,mimetypes,os,re,secrets,sys,threading,time,uuid,zipfile",
        "import base64,io,json,math,mimetypes,os,re,secrets,subprocess,sys,threading,time,uuid,zipfile",
    )

old = "m=re.fullmatch(r'/api/jobs/([a-f0-9]{32})/(cancel|retry)',path)"
new = "m=re.fullmatch(r'/api/jobs/([a-f0-9]{32})/(cancel|retry|reveal)',path)"
if old not in text:
    raise SystemExit("cancel|retry pattern missing")
text = text.replace(old, new)

if "action=='reveal'" not in text.replace(" ", ""):
    lines = text.splitlines(True)
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        compact = line.replace(" ", "")
        if "ifaction=='cancel':" in compact:
            i += 1
            while i < len(lines) and "action=='retry'" not in lines[i].replace(" ", ""):
                out.append(lines[i])
                i += 1
            out.append("     if action=='reveal':\n")
            out.append("      focus=job/'output.glb'\n")
            out.append("      if focus.is_file():\n")
            out.append(
                "       subprocess.Popen(['explorer','/select,',str(focus)],creationflags=subprocess.CREATE_NO_WINDOW)\n"
            )
            out.append("      else:\n")
            out.append(
                "       subprocess.Popen(['explorer',str(job)],creationflags=subprocess.CREATE_NO_WINDOW)\n"
            )
            out.append("      return self.response(200,{'ok':True,'path':str(job)})\n")
            continue
        i += 1
    text = "".join(out)

if "/api/open_jobs" not in text:
    marker = "if path=='/api/config':"
    if marker not in text:
        raise SystemExit("config marker missing")
    add = (
        "if path=='/api/open_jobs':\n"
        "   subprocess.Popen(['explorer',str(JOBS)],creationflags=subprocess.CREATE_NO_WINDOW);"
        "return self.response(200,{'ok':True,'path':str(JOBS)})\n"
        "  "
    )
    text = text.replace(marker, add + marker)

p.write_text(text, encoding="utf-8")
print("patched", p)
print("has_reveal", "action=='reveal'" in text.replace(" ", ""))
print("has_open_jobs", "/api/open_jobs" in text)

from pathlib import Path
p = Path("desktop/server.py")
text = p.read_text(encoding="utf-8")
needle = "     s={'quality':quality,'triangles':triangles,'height_cm':height,'texture_size':res,'textures':settings.get('textures',True),'face':settings.get('face',False),'rig':settings.get('rig',False),'seed':42}\n     if s['face'] and not s['textures']:raise ValueError('Gesichtsdetails erfordern Texturen.')\n"
insert = """     s={'quality':quality,'triangles':triangles,'height_cm':height,'texture_size':res,'textures':settings.get('textures',True),'face':settings.get('face',False),'rig':settings.get('rig',False),'seed':42}
     # Opt-in finalize lineage (default OFF). Not a Studio UI default.
     fc=settings.get('finalize_candidate')
     if fc not in (None, False, ''):
      if not isinstance(fc,str) or not fc.strip():raise ValueError('finalize_candidate muss ein job-relativer Pfad sein.')
      rel=fc.strip().replace('\\\\','/').lstrip('/')
      if Path(rel).is_absolute() or '..' in Path(rel).parts:raise ValueError('finalize_candidate muss im Job-Ordner bleiben.')
      s['finalize_candidate']=rel
     fs=settings.get('face_source')
     if isinstance(fs,str) and fs.strip():s['face_source']=fs.strip()
     if s['face'] and not s['textures']:raise ValueError('Gesichtsdetails erfordern Texturen.')
"""
# In the insert string above, '\\\\' in the source file should be a Python string with one backslash doubled for replace
# We want the server.py line to contain: rel=fc.strip().replace('\\','/')
# In a Python triple-quoted string writing that, we need: replace('\\\\','/')
# Wait - in the ''' string for insert, \\\\ becomes \\ in the output file, which is correct for Python source replace('\\','/')
if needle not in text:
    # try CRLF
    needle2 = needle.replace("\n", "\r\n")
    if needle2 not in text:
        raise SystemExit("needle not found")
    text = text.replace(needle2, insert.replace("\n", "\r\n"))
else:
    text = text.replace(needle, insert)
p.write_text(text, encoding="utf-8")
print("server.py patched")
# verify
t2 = p.read_text(encoding="utf-8")
assert "finalize_candidate" in t2
print("ok")

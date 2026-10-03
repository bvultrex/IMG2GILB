from pathlib import Path

js_path = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\web\app.js")
js = js_path.read_text(encoding="utf-8")
if "interim studio helpers" in js:
    print("already patched")
else:
    extra = r"""

// --- interim studio helpers (Grok 2026-09-28) ---
(function(){
  const g = id => document.getElementById(id);
  const preset = g('presetCharacter');
  if (preset) preset.onclick = () => {
    g('quality').value = 'standard';
    g('triangles').value = 100000;
    g('height').value = 170;
    g('resolution').value = 2048;
    g('textures').checked = true;
    g('face').checked = true;
    g('textures').onchange();
    storeDraft();
    g('draftStatus').textContent = 'Preset Charakter Standard geladen.';
  };
  const loadBtn = g('loadFolder');
  const picker = g('folderPicker');
  if (loadBtn && picker) {
    loadBtn.onclick = () => picker.click();
    picker.onchange = () => {
      const list = [...picker.files];
      const map = {front:null, back:null, left:null, right:null};
      for (const f of list) {
        const n = f.name.toLowerCase();
        if (/front|vorn/.test(n)) map.front = f;
        else if (/back|hinten|rear/.test(n)) map.back = f;
        else if (/left|links|side_a/.test(n)) map.left = f;
        else if (/right|rechts|side_b/.test(n)) map.right = f;
      }
      let loaded = 0;
      for (const [k, f] of Object.entries(map)) if (f) { setReference(k, f); loaded++; }
      storeDraft();
      if (!map.front) error('Ordner braucht mindestens front.png (oder Namen mit front/vorn).');
      else { g('draftStatus').textContent = loaded + ' Ansicht(en) aus Ordner geladen.'; error(''); }
    };
  }
  const openFolder = g('openFolder');
  if (openFolder) openFolder.onclick = async () => {
    try {
      if (!current) throw Error('Kein Projekt gewaehlt.');
      await api('/api/jobs/' + current + '/reveal', {});
    } catch (e) { error(e.message); }
  };
  const openJobs = g('openJobsRoot');
  if (openJobs) openJobs.onclick = async () => {
    try { await api('/api/open_jobs'); } catch (e) { error(e.message); }
  };
})();
"""
    js_path.write_text(js + extra, encoding="utf-8")
    print("appended")

# Ensure HTML has openFolder + openJobsRoot buttons
html_path = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\web\index.html")
html = html_path.read_text(encoding="utf-8")
if 'id="openFolder"' not in html:
    # insert after saveProject anchor
    needle = 'id="saveProject" download="IMG2GILB-Projekt.zip">Projekt speichern</a>'
    if needle not in html:
        raise SystemExit("saveProject needle missing")
    html = html.replace(
        needle,
        needle
        + '<button id="openFolder" type="button">Ordner oeffnen</button>'
        + '<button id="openJobsRoot" type="button">Alle Projekte</button>',
    )
    html_path.write_text(html, encoding="utf-8")
    print("html buttons added")
else:
    print("html already has openFolder")
print("openFolder", 'id="openFolder"' in html_path.read_text(encoding="utf-8"))
print("openJobsRoot", 'id="openJobsRoot"' in html_path.read_text(encoding="utf-8"))
print("preset", 'id="presetCharacter"' in html_path.read_text(encoding="utf-8"))

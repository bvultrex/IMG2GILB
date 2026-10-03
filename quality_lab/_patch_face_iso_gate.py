from pathlib import Path
paths = [
    Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\project_hybrid_a3.py"),
    Path(r"D:\SF3D_QualityLab\project_hybrid_a3.py"),
]
old = '''    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(dx) <= 36
        and abs(dy) <= 36
        and 0.90 <= scale <= 1.12
        and nin >= max(3, len(sk_use) // 2)
    )'''
new = '''    # Prefer residual quality over absolute translation: large dx/dy is OK if landmarks fit tightly.
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(dx) <= 96
        and abs(dy) <= 96
        and 0.90 <= scale <= 1.12
        and nin >= max(3, len(sk_use) // 2)
    )'''
# Also allow larger delta application in face_iso block
old2 = '''            if abs(Mq[0, 1]) < 0.08 and abs(Mq[1, 0]) < 0.08 and abs(dx) <= 28 and abs(dy) <= 28:
                delta = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32)
                meta["chosen"] = "face_iso_landmark_translation"
            elif abs(dx) <= 28 and abs(dy) <= 28 and 0.92 <= scale <= 1.08:
                delta = Mq
                meta["chosen"] = "face_iso_landmark_partial_affine"'''
new2 = '''            # Cap applied motion to 48px / small scale; clamp if larger but gate passed
            if abs(Mq[0, 1]) < 0.08 and abs(Mq[1, 0]) < 0.08:
                c = min(1.0, 48.0 / max(abs(dx), abs(dy), 1e-3))
                delta = np.array([[1.0, 0.0, dx * c], [0.0, 1.0, dy * c]], dtype=np.float32)
                meta["chosen"] = "face_iso_landmark_translation" + ("_clamped" if c < 1.0 else "")
                meta["clamp_scale"] = float(c)
            elif 0.92 <= scale <= 1.08:
                c = min(1.0, 48.0 / max(abs(dx), abs(dy), 1e-3))
                Mq2 = Mq.copy()
                Mq2[0, 2] *= c
                Mq2[1, 2] *= c
                delta = Mq2
                meta["chosen"] = "face_iso_landmark_partial_affine" + ("_clamped" if c < 1.0 else "")
                meta["clamp_scale"] = float(c)'''
# When face_iso project_face False after gate, clear earlier face_center delta so we don't warp then paint
old3 = '''        elif not q.get("ok"):
            meta["chosen"] = meta.get("chosen") or "face_iso_paint_fallback"
            meta["steps"].append({"mode": "face_iso_gate_fail", "reason": q.get("reason")})'''
new3 = '''        elif not q.get("ok"):
            delta = None  # coherent Paint face: no micro warp of mismatched ortho
            meta["chosen"] = "face_iso_paint_fallback"
            meta["steps"].append({"mode": "face_iso_gate_fail", "reason": q.get("reason")})'''

# Prefer landmark affine over earlier face_center when face_iso ok
old4 = '''        if q.get("ok") and delta is None and "affine" in q:'''
new4 = '''        if q.get("ok") and "affine" in q:
            # Landmark registration overrides prior face_center guess'''

for p in paths:
    t = p.read_text(encoding='utf-8')
    for a,b,name in [(old,new,'gate'),(old2,new2,'apply'),(old3,new3,'clear'),(old4,new4,'override')]:
        if b.strip()[:40] in t and name != 'override':
            # idempotent soft check
            pass
        if a not in t:
            print(f"MISSING {name} in {p}")
        else:
            t = t.replace(a,b,1)
            print(f"OK {name} {p.name}")
    p.write_text(t, encoding='utf-8')
print('patched')

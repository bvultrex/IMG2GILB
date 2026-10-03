from pathlib import Path
PATHS = [
    Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab\project_hybrid_a3.py"),
    Path(r"D:\SF3D_QualityLab\project_hybrid_a3.py"),
]
old = '''    # Scale-independent face shift from detector bboxes (do NOT gate on raw M[:,2] when scale≠1)
    center_dx = center_dy = None
    if sb is not None and db is not None:
        center_dx = float(((db[0] + db[2]) * 0.5) - ((sb[0] + sb[2]) * 0.5))
        center_dy = float(((db[1] + db[3]) * 0.5) - ((sb[1] + sb[3]) * 0.5))
    # Gate translation on center delta when available; fall back to raw only if |scale-1|<=0.02
    if center_dx is not None:
        t_dx, t_dy = center_dx, center_dy
    elif abs(scale - 1.0) <= 0.02:
        t_dx, t_dy = dx, dy
    else:
        t_dx, t_dy = dx, dy  # will fail the tighter 24px gate when scale invents large tx
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(t_dx) <= 24
        and abs(t_dy) <= 24
        and 0.90 <= scale <= 1.12
        and nin >= max(3, len(sk_use) // 2)
    )
'''
new = '''    # Scale-independent face shift from detector bboxes (do NOT gate on raw M[:,2] when scale≠1)
    center_dx = center_dy = None
    if sb is not None and db is not None:
        center_dx = float(((db[0] + db[2]) * 0.5) - ((sb[0] + sb[2]) * 0.5))
        center_dy = float(((db[1] + db[3]) * 0.5) - ((sb[1] + sb[3]) * 0.5))
    # Gate: residual + scale + inliers. Translation magnitude uses center (≤48, matches
    # face_center_translation); extract clamps applied delta to 24. Raw M[:,2] only when scale≈1.
    if center_dx is not None:
        t_dx, t_dy = center_dx, center_dy
        t_lim = 48.0
    elif abs(scale - 1.0) <= 0.02:
        t_dx, t_dy = dx, dy
        t_lim = 24.0
    else:
        # Scaled similarity without bboxes: raw tx untrustworthy → fail gate (paint fallback)
        t_dx, t_dy = dx, dy
        t_lim = 0.0  # force fail unless somehow zero
    ok = (
        med <= 6.0
        and p90 <= 12.0
        and abs(t_dx) <= t_lim
        and abs(t_dy) <= t_lim
        and 0.90 <= scale <= 1.12
        and nin >= max(3, len(sk_use) // 2)
    )
'''
for p in PATHS:
    t = p.read_text(encoding='utf-8')
    if old not in t:
        raise SystemExit(f'missing block in {p}')
    p.write_text(t.replace(old, new, 1), encoding='utf-8')
    print('ok', p)

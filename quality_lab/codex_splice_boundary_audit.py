"""Read-only topology audit; never hides distant boundaries to improve coverage."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def audit(mesh):
    indexed = np.sort(np.concatenate([mesh.faces[:, [0, 1]], mesh.faces[:, [1, 2]], mesh.faces[:, [2, 0]]]), axis=1)
    _, indexed_counts = np.unique(indexed, axis=0, return_counts=True)
    # GLB may split vertices at normals/UVs. Diagnose positional topology too.
    _, remap = np.unique(np.round(mesh.vertices, 7), axis=0, return_inverse=True)
    faces = remap[mesh.faces]
    edges = np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
    edges, counts = np.unique(edges, axis=0, return_counts=True)
    boundary = edges[counts == 1]
    result = dict(triangles=len(faces), positional_vertices=int(remap.max()+1),
                  boundary_edges=len(boundary), nonmanifold_edges=int((counts > 2).sum()),
                  indexed_boundary_edges=int((indexed_counts == 1).sum()),
                  indexed_nonmanifold_edges=int((indexed_counts > 2).sum()))
    if len(boundary):
        ids, inverse = np.unique(boundary, return_inverse=True)
        e = inverse.reshape(-1, 2)
        graph = coo_matrix((np.ones(len(e)*2), (np.r_[e[:,0], e[:,1]], np.r_[e[:,1], e[:,0]])), shape=(len(ids), len(ids))).tocsr()
        n, labels = connected_components(graph)
        degree = np.asarray(graph.sum(axis=1)).ravel()
        result.update(boundary_components=int(n), closed_simple_loops=sum(bool(np.all(degree[labels == i] == 2)) for i in range(n)),
                      branched_boundary_vertices=int((degree > 2).sum()), boundary_endpoints=int((degree == 1).sum()))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('models', nargs='+', type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    reports = []
    for path in a.models:
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        scene = trimesh.load(path, force='scene', process=False)
        reports.append(dict(path=str(path.resolve()), sha256=sha,
                            geometries={name: audit(mesh) for name, mesh in scene.geometry.items()},
                            scope='All positional boundaries, including preexisting defects; not a seam-distance or intersection gate'))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps(reports, indent=2))

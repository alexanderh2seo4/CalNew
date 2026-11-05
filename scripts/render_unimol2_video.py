"""Render a short MP4 of the Uni-Mol2 feature calculation used by the modular pipeline.

Terminal look: pure black, no boxes or axes, one typed command line per scene. Every
visual is computed live with the pipeline's settings (ETKDGv3 seed 42, 32 conformers,
MMFF94, 0.5 A RMS filter, 16 retained, frozen Uni-Mol2 84M, mean pooling, 256-bit chiral
Morgan fingerprint). The only illustrative element is the morph from random start to the
embedded geometry, flagged in its command line: ETKDG's internal steps are not exposed.

Needs an ffmpeg binary, e.g. from `imageio-ffmpeg` on PYTHONPATH.
"""
import argparse
import datetime
import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from rdkit import Chem
from rdkit.Chem import AllChem, Draw, rdMolAlign

BG, INK, DIM, PROMPT, CYAN, AMBER = "#000000", "#d4d4d4", "#5c5c5c", "#3ddc84", "#4fd6ff", "#ffb347"
ELEMENT = {"C": ("#b8b8b8", 60), "O": ("#ff5f56", 80), "N": ("#4f8fe8", 75), "S": ("#ffd84f", 90), "H": ("#8a8a8a", 16)}
FPS, W, H, DPI = 24, 1280, 720, 100
FONT, SIZE = "DejaVu Sans Mono", 15
SIGNED = LinearSegmentedColormap.from_list("signed", [CYAN, BG, AMBER])
CHAR = 0.6 * SIZE / 72 * DPI / W  # monospace advance as a figure fraction


def figure():
    return plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=BG)


def frame(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()


def cli(fig, command, k, result="", type_seconds=0.9):
    """One typed terminal line: prompt, command (typed out), optional live result, cursor."""
    typed = command[: int(len(command) * min(1.0, k / (type_seconds * FPS)))]
    renderer = fig.canvas.get_renderer()
    y = 0.07

    def put(x, text, color):
        artist = fig.text(x, y, text, color=color, fontsize=SIZE, family=FONT, va="center")
        return artist.get_window_extent(renderer).x1 / W if text else x

    tail = put(0.05, "$", PROMPT) + CHAR
    tail = put(tail, typed, INK)
    if len(typed) == len(command) and result:
        tail = put(tail + 2 * CHAR, result, CYAN)
    if (k // (FPS // 2)) % 2 == 0:
        put(tail + 0.4 * CHAR, "█", INK)


def note(where, x, y, text, color=DIM, size=10, **kw):
    """Small grey monospace annotation (figure fractions on a figure, data coords on axes)."""
    return where.text(x, y, text, color=color, fontsize=size, family=FONT, **kw)


def bare(ax):
    ax.set_facecolor(BG)
    ax.set_axis_off()


def draw_molecule(ax, mol, xyz, azim, alpha=1.0, bond_color="#c8c8c8", lw=2.2, atoms=True, zoom=4.2):
    ax.set_facecolor(BG)
    for b in mol.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        ax.plot(*xyz[[i, j]].T, color=bond_color, lw=lw * (1.4 if b.GetBondTypeAsDouble() == 2 else 1), alpha=alpha, solid_capstyle="round")
    if atoms:
        for a in mol.GetAtoms():
            color, size = ELEMENT.get(a.GetSymbol(), ("#c07adf", 70))
            ax.scatter(*xyz[a.GetIdx()], s=size * 2.2, color=color, edgecolor=BG, linewidth=0.6, alpha=alpha, depthshade=False)
    c = xyz.mean(0)
    for setter, v in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), c):
        setter(v - zoom, v + zoom)
    ax.view_init(elev=18, azim=azim)
    ax.set_axis_off()


def scene_title(mol2d, smiles, name, seconds=3.5):
    img = Draw.MolToImage(mol2d, size=(560, 430), kekulize=True, wedgeBonds=True)
    arr = 1 - np.asarray(img.convert("L")).astype(float) / 255  # white lines on black
    rgb = np.clip(np.stack([arr] * 3, -1) * 0.9, 0, 1)
    from rdkit.Chem import Descriptors, rdMolDescriptors
    centres = Chem.FindMolChiralCenters(mol2d, includeUnassigned=True)
    facts = (f"{rdMolDescriptors.CalcMolFormula(mol2d)}  ·  {Descriptors.MolWt(mol2d):.2f} g/mol  ·  "
             f"{len(centres)} stereocentre ({', '.join(c for _, c in centres)})  ·  {Descriptors.NumRotatableBonds(mol2d)} rotatable bonds")
    for k in range(int(seconds * FPS)):
        fig = figure()
        ax = fig.add_axes([0.28, 0.2, 0.44, 0.68])
        ax.imshow(rgb)
        bare(ax)
        note(fig, 0.5, 0.17, facts, ha="center")
        cli(fig, f'calnew embed "{smiles}"', k, f"# {name}")
        yield frame(fig)
        plt.close(fig)


def mmff_trajectory(mol, conf_id):
    props = AllChem.MMFFGetMoleculeProperties(mol)
    ff = AllChem.MMFFGetMoleculeForceField(mol, props, confId=conf_id)
    ff.Initialize()
    traj, energy = [np.array(ff.Positions()).reshape(-1, 3)], [ff.CalcEnergy()]
    for _ in range(500):
        more = ff.Minimize(maxIts=1)
        traj.append(np.array(ff.Positions()).reshape(-1, 3))
        energy.append(ff.CalcEnergy())
        if more == 0:
            break
    return np.array(traj), np.array(energy)


def ensemble(mol, seed=42, generated=32, retained=16, cutoff=0.5):
    params = AllChem.ETKDGv3()
    params.randomSeed, params.numThreads, params.enforceChirality = seed, 1, True
    ids = list(AllChem.EmbedMultipleConfs(mol, numConfs=generated, params=params))
    opt = AllChem.MMFFOptimizeMoleculeConfs(mol, numThreads=1, maxIters=500)
    valid = [i for i in ids if opt[i][0] == 0 and np.isfinite(opt[i][1])]
    keep = []
    for i in sorted(valid, key=lambda j: opt[j][1]):
        if all(rdMolAlign.GetBestRMS(mol, mol, prbId=i, refId=j) >= cutoff for j in keep):
            keep.append(i)
        if len(keep) >= retained:
            break
    ref = keep[0]
    heavy = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() > 1]
    for i in ids:
        rdMolAlign.AlignMol(mol, mol, prbCid=i, refCid=ref, atomMap=[(a, a) for a in heavy])
    energies = np.array([opt[i][1] for i in ids])
    return mol, ids, keep, energies, {i: mol.GetConformer(i).GetPositions() for i in ids}


def unimol_vectors(mol, keep):
    import torch
    from huggingface_hub import hf_hub_download
    from unimol_tools import UniMolRepr
    from calnew.chemistry import fingerprints
    torch.set_num_threads(4)
    weights = hf_hub_download("dptech/Uni-Mol2", "modelzoo/84M/checkpoint.pt", revision="bf37d253c0f5ac61f468137eb00059978a104ff0",
                              cache_dir=str(Path("data/checkpoints").resolve()))
    model = UniMolRepr(data_type="molecule", model_name="unimolv2", model_size="84m", remove_hs=False, use_cuda=False,
                       batch_size=4, pretrained_model_path=weights)
    atoms = [a.GetSymbol() for a in mol.GetAtoms()]
    coords = [mol.GetConformer(i).GetPositions() for i in keep]
    out = model.get_repr({"atoms": [atoms] * len(coords), "coordinates": coords})
    per = np.asarray(out["cls_repr"] if isinstance(out, dict) else out)
    chiral = fingerprints([Chem.MolToSmiles(Chem.RemoveHs(mol))], size=256)[0]
    return per, chiral


def scene_fit(mol, start_xyz, seconds_morph=2.5, seconds_opt=6.0):
    rng = np.random.default_rng(3)
    random_xyz = rng.uniform(-4, 4, size=start_xyz.shape) + start_xyz.mean(0)
    traj, energy = mmff_trajectory(Chem.Mol(mol), 0)
    n_morph, n_opt = int(seconds_morph * FPS), int(seconds_opt * FPS)
    for k in range(n_morph):
        t = (1 - np.cos(np.pi * k / (n_morph - 1))) / 2
        fig = figure()
        ax = fig.add_axes([0.02, 0.12, 0.6, 0.85], projection="3d")
        draw_molecule(ax, mol, (1 - t) * random_xyz + t * start_xyz, 30 + k * 0.6)
        note(fig, 0.32, 0.2, f"{mol.GetNumAtoms()} atoms  ·  {mol.GetNumHeavyAtoms()} heavy  ·  chirality enforced", ha="center")
        cli(fig, "etkdg --seed 42", k, "# random start -> embedded (illustrative morph)")
        yield frame(fig)
        plt.close(fig)
    index = np.unique(np.linspace(0, len(traj) - 1, n_opt).astype(int))
    for k, i in enumerate(np.concatenate([index, np.repeat(index[-1], FPS)])):
        fig = figure()
        ax = fig.add_axes([0.02, 0.12, 0.6, 0.85], projection="3d")
        draw_molecule(ax, mol, traj[i], 30 + (n_morph + k) * 0.6)
        ax2 = fig.add_axes([0.64, 0.3, 0.3, 0.45])
        bare(ax2)
        ax2.plot(np.arange(i + 1), energy[: i + 1], color=CYAN, lw=1.6)
        ax2.scatter([i], [energy[i]], color=AMBER, s=24, zorder=3)
        ax2.set_xlim(0, len(energy))
        ax2.set_ylim(energy.min() - 2, energy.max() + 2)
        base = energy.min() - 2
        ax2.plot([0, len(energy)], [base, base], color="#262626", lw=0.8)
        note(ax2, 0, energy[0], f"{energy[0]:.1f} ", ha="right", va="center")
        note(ax2, i, energy[i], f"  {energy[i]:.2f}", color=AMBER, va="bottom")
        note(ax2, 0, base, "0", va="top", ha="center")
        note(ax2, len(energy), base, str(len(energy) - 1), va="top", ha="center")
        note(ax2, len(energy) / 2, base, "iterations", va="top", ha="center")
        note(ax2, 0, energy.max() + 2, "kcal/mol", va="bottom")
        note(fig, 0.32, 0.2, "bonds · angles · torsions · van der Waals · electrostatics", ha="center")
        cli(fig, "mmff94 --minimize", k, f"E = {energy[i]:6.2f} kcal/mol  iter {i}", type_seconds=0.6)
        yield frame(fig)
        plt.close(fig)


def scene_ensemble(mol, ids, keep, energies, coords, seconds_in=5.0, seconds_filter=3.5):
    rel = energies - energies.min()
    order = np.argsort(energies)
    heavy = Chem.RemoveHs(mol)
    heavy_idx = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() > 1]
    n_in, n_f = int(seconds_in * FPS), int(seconds_filter * FPS)
    for k in range(n_in + n_f):
        shown = min(len(ids), 1 + int(len(ids) * k / (n_in * 0.85)))
        filtering = k >= n_in
        fig = figure()
        ax = fig.add_axes([0.0, 0.12, 0.6, 0.85], projection="3d")
        ax.set_facecolor(BG)
        for i in ids[:shown]:
            kept = i in keep
            color = CYAN if (kept or not filtering) else "#2a2a2a"
            alpha = 0.9 if kept and filtering else (0.25 if filtering else 0.35)
            draw_molecule(ax, heavy, coords[i][heavy_idx], 30 + k * 0.8, alpha=alpha, bond_color=color, lw=1.4, atoms=False, zoom=5.0)
        ax2 = fig.add_axes([0.64, 0.3, 0.3, 0.45])
        bare(ax2)
        colors = [(CYAN if i in keep else "#2a2a2a") if filtering else AMBER for i in np.array(ids)[order]]
        ax2.bar(np.arange(len(ids)), np.where(np.arange(len(ids)) < shown, rel[order] + 0.03, 0), color=colors, width=0.7)
        ax2.set_ylim(0, max(rel.max() * 1.1, 1))
        ax2.set_xlim(-1, len(ids))
        note(ax2, -1, 0, "0 ", ha="right", va="center")
        if shown == len(ids):
            note(ax2, len(ids) - 1, rel.max() + 0.03, f"{rel.max():.2f}", ha="center", va="bottom")
        note(ax2, len(ids) / 2, -0.04 * rel.max(), "ΔE kcal/mol · sorted by energy", ha="center", va="top")
        if filtering:
            note(ax2, 0, rel.max() * 1.02, f"kept {len(keep)}", color=CYAN, va="bottom")
            note(ax2, 0, rel.max() * 0.92, f"near-duplicates {len(ids) - len(keep)}", va="bottom")
        note(fig, 0.3, 0.2, "aligned on heavy atoms  ·  keep if RMS ≥ 0.5 Å to every kept one", ha="center")
        result = f"{shown}/{len(ids)} conformers" + (f" -> {len(keep)} kept" if filtering else "")
        cli(fig, "etkdg --confs 32 | mmff94 | rms-filter 0.5A", k, result)
        yield frame(fig)
        plt.close(fig)


def scene_encoder(per, chiral, seconds_rows=4.5, seconds_pool=4.0):
    n, d = per.shape
    lim = np.quantile(np.abs(per), 0.98)
    mean = per.mean(0)
    cos = per @ mean / (np.linalg.norm(per, axis=1) * np.linalg.norm(mean))
    n_rows, n_pool = int(seconds_rows * FPS), int(seconds_pool * FPS)
    for k in range(n_rows + n_pool):
        rows = min(n, 1 + int(n * k / (n_rows * 0.85)))
        pooling = k >= n_rows
        fig = figure()
        ax = fig.add_axes([0.08, 0.42, 0.84, 0.46])
        shown = np.zeros_like(per)
        shown[:rows] = per[:rows]
        ax.imshow(shown, aspect="auto", cmap=SIGNED, vmin=-lim, vmax=lim, interpolation="nearest")
        bare(ax)
        note(fig, 0.075, 0.87, "conf 1", ha="right", va="center")
        note(fig, 0.075, 0.43, f"conf {n}", ha="right", va="center")
        note(fig, 0.08, 0.40, "0", va="top")
        note(fig, 0.92, 0.40, str(d - 1), va="top", ha="right")
        note(fig, 0.5, 0.40, "CLS dimension", va="top", ha="center")
        note(fig, 0.80, 0.9, f"-{lim:.1f}", color=CYAN, ha="right", va="bottom")
        note(fig, 0.86, 0.9, "0", ha="right", va="bottom")
        note(fig, 0.92, 0.9, f"+{lim:.1f}", color=AMBER, ha="right", va="bottom")
        result = f"{rows} x {d}"
        if pooling:
            t = min(1.0, (k - n_rows) / (0.6 * n_pool))
            split = 0.84 * d / (d + 256)
            ax4 = fig.add_axes([0.08, 0.22, split, 0.08])
            ax4.imshow(mean[None, :], aspect="auto", cmap=SIGNED, vmin=-lim, vmax=lim, alpha=t)
            bare(ax4)
            ax5 = fig.add_axes([0.08 + split + 0.006, 0.22, 0.84 - split - 0.006, 0.08])
            ax5.imshow(chiral[None, :], aspect="auto", cmap=LinearSegmentedColormap.from_list("bits", [BG, PROMPT]), vmin=0, vmax=1, alpha=t)
            bare(ax5)
            note(fig, 0.08, 0.205, f"mean of {n} conformers · {d}", va="top", alpha=t)
            note(fig, 0.08 + split + 0.006, 0.205, "chiral fp · 256", va="top", alpha=t, color=PROMPT)
            note(fig, 0.92, 0.32, f"= {d + 256} features", va="bottom", ha="right", alpha=t, color=INK)
            result = f"{n} x {d} -> mean + chiral-fp -> {d + 256}   (min cos {cos.min():.4f})"
        cli(fig, "unimol2 --frozen --pool mean", k, result)
        yield frame(fig)
        plt.close(fig)


def scene_progress(total, seconds=6.0):
    from sklearn.manifold import TSNE
    items = []
    for meta in Path("data/features/unimol2").glob("*.json"):
        npy = meta.with_suffix(".npy")
        if npy.exists() and "settings" in (info := json.loads(meta.read_text())):
            items.append((npy.stat().st_mtime, info["smiles"], np.load(npy)[:768]))
    items.sort(key=lambda t: t[0])
    x = np.stack([v for _, _, v in items])
    xy = TSNE(n_components=2, perplexity=30, init="pca", random_state=0).fit_transform((x - x.mean(0)) / (x.std(0) + 1e-6))
    atoms = np.array([Chem.MolFromSmiles(s).GetNumHeavyAtoms() for _, s, _ in items])
    cmap = LinearSegmentedColormap.from_list("dots", ["#1f6f8b", CYAN, "#ffffff"])
    n_frames = int(seconds * FPS)
    for k in range(n_frames + FPS):
        shown = min(len(items), 1 + int(len(items) * k / n_frames))
        fig = figure()
        ax = fig.add_axes([0.12, 0.16, 0.76, 0.78])
        bare(ax)
        ax.scatter(xy[:shown, 0], xy[:shown, 1], c=atoms[:shown], cmap=cmap, vmin=atoms.min(), vmax=np.quantile(atoms, 0.98), s=9, edgecolor="none")
        ax.scatter(xy[shown - 1, 0], xy[shown - 1, 1], s=70, facecolor="none", edgecolor=AMBER, lw=1.4)
        ax.set_xlim(xy[:, 0].min() - 3, xy[:, 0].max() + 3)
        ax.set_ylim(xy[:, 1].min() - 3, xy[:, 1].max() + 3)
        note(ax, xy[shown - 1, 0], xy[shown - 1, 1], "   " + items[shown - 1][1][:34], color=AMBER, va="center", size=9)
        note(fig, 0.05, 0.93, "t-SNE of 768-d Uni-Mol2 vectors · perplexity 30", va="center")
        note(fig, 0.95, 0.93, f"heavy atoms {atoms.min()}", color="#1f6f8b", ha="right", va="center")
        note(fig, 0.95, 0.90, f"→ {int(np.quantile(atoms, 0.98))}+", color="#ffffff", ha="right", va="center")
        cli(fig, "calnew embed --all | tsne", k, f"{shown:,}/{total:,} molecules")
        yield frame(fig)
        plt.close(fig)



def main():
    p = argparse.ArgumentParser()
    p.add_argument("--smiles", default="CC(C)=CCC[C@@](C)(O)C=C")
    p.add_argument("--name", default="(R)-linalool")
    p.add_argument("--total", type=int, default=2725)
    p.add_argument("--out", type=Path, default=Path("docs/media/unimol2-calculation.mp4"))
    a = p.parse_args()
    import imageio_ffmpeg
    mol2d = Chem.MolFromSmiles(a.smiles)
    mol = Chem.AddHs(mol2d)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    single = Chem.Mol(mol)
    AllChem.EmbedMolecule(single, params)
    ens_mol, ids, keep, energies, coords = ensemble(Chem.Mol(mol))
    per, chiral = unimol_vectors(ens_mol, keep)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(a.out), (W, H), fps=FPS, codec="libx264", quality=8, macro_block_size=8,
                                         output_params=["-movflags", "+faststart"])
    writer.send(None)
    count = 0
    scenes = [scene_title(mol2d, a.smiles, a.name), scene_fit(single, single.GetConformer().GetPositions()),
              scene_ensemble(ens_mol, ids, keep, energies, coords), scene_encoder(per, chiral), scene_progress(a.total)]
    for scene in scenes:
        for img in scene:
            writer.send(img)
            count += 1
    writer.close()
    print(json.dumps({"out": str(a.out), "frames": count, "seconds": round(count / FPS, 1), "conformers": len(ids), "retained": len(keep),
                      "unimol_dim": int(per.shape[1]), "mb": round(os.path.getsize(a.out) / 1e6, 2)}))


if __name__ == "__main__":
    main()

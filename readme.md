# Large-Scale Early / In-Season Crop Type Mapping

**Final Year Project — MachVis Lab (NUST) in collaboration with NARC & DAAD, Germany**
**Awarded: Flagship Project**

This repository contains the complete framework, preprocessing pipeline, model code, and scripts used in my Final Year Project on **large-scale crop type mapping** across **Punjab and Sindh** using satellite imagery.

The project focuses on **operational, in-season crop monitoring at 30m resolution** using multispectral imagery and state-of-the-art **ViT-based semantic segmentation** models.
All results—including provincial maps, district crops, stitched tiles, JSON outputs, and RGB renderings—are generated using this framework.

---

## 🚀 Project Summary

* Developed a **large-scale, end-to-end pipeline** for classifying crops across Pakistan using 20GB+ of seasonal satellite data.
* Implemented domain adaptation between **US → Uzbekistan → Pakistan**, addressing the fundamental challenge of limited labeled data in Pakistan.
* Fine-tuned **Satlas-Pretrain Vision Transformer (ViT)** segmentation head for **5 classes**:
  **Cotton, Wheat, Urban, Natural, Others**
* Achieved **state-of-the-art accuracy: 79.3% Overall Accuracy**.
* Deployed a scalable inference pipeline capable of generating full-province crop maps.
* Produced high-resolution district PNGs, stitched tiles, JSON summaries, and statistical outputs.

---

## 🌍 Key Outputs

The framework generates:

* **Seasonal crop maps** for Punjab & Sindh
* **District-level cropped PNGs**
* **Tile-wise stitched TIFs/PNGs**
* **JSON summaries of crop distributions**
* **Province-wide composite maps**
* **RGB visualizations for inspection**

Example seasons included in this repository:

* `Jan-Apr 2025`
* `Jun-Dec 2024`

---

## 📁 Repository Structure

A simplified overview of the repository (excluding large datasets):

```
├── api/
│   ├── model/
│   └── routes/
│       └── map.py
├── model/
│   ├── model.py
│   └── unet_best.pth
├── dataloader.py
├── createMasks.py
├── createOutputMap.py
├── createLargeOutputMap.py
├── downloadTileEarthAccess.py
├── patchifyTileForPrithvi.py
├── stitch256masks.py
├── tiffToCroppedPngs.py
├── tiffToPunjabPng.py
├── tiffToSindhPng.py
├── viz.py / viz2.py
├── main.py
├── util/
├── bandspng/                  # 16-band inputs visualized
├── mapdata/                   # District outputs, stitched tiles, JSON stats
├── requirements.txt
└── readme.md
```

> **Note:** Large imagery, stitched tiles, and JSON outputs are included for reference but not needed for inference if using your own data.

---

## 🧠 Model Details

### ✦ Backbone

**Satlas-Pretrain Vision Transformer (ViT)** — pretrained on global multi-sensor satellite imagery.

### ✦ Fine-tuning Setup

* 30m spatial resolution
* 16 multispectral bands
* 5-way semantic segmentation
* Optimized loss for highly imbalanced crop distribution

### ✦ Target Classes

| Label | Class   |
| ----- | ------- |
| 0     | Other   |
| 1     | Cotton  |
| 2     | Wheat   |
| 3     | Urban   |
| 4     | Natural |

---

## 🔧 Processing & Inference Pipeline

The workflow consists of:

1. **Tile Downloading**
   `downloadTileEarthAccess.py`

2. **Patchification**
   `patchifyTileForPrithvi.py`

3. **Model Inference**
   `main.py`
   (Loads `unet_best.pth`, runs inference tile-by-tile)

4. **Mask Generation**
   `createMasks.py`

5. **Stitching Outputs**
   `stitch256masks.py`
   → Produces district-level and province-level maps

6. **JSON Summary Generation**
   `viz.py`, `viz2.py`
   → Extracts per-class stats

7. **Cropped PNG Generation**
   `tiffToPunjabPng.py`, `tiffToSindhPng.py`

---

## ▶️ Running Inference

Install dependencies:

```bash
pip install -r requirements.txt
```

Run inference on satellite tiles:

```bash
python main.py --input <tile_folder> --output <output_folder>
```

Generate stitched province outputs:

```bash
python createLargeOutputMap.py
```

Create district PNGs:

```bash
python tiffToCroppedPngs.py
```

---

## 📊 Visualization Examples

The repo includes:

* `bandspng/` — 16-band visualizations
* `stitched_tile_*.png` — stitched seasonal outputs
* `jsonData/` — crop statistics per district
* `croppedPngs/` — final export-ready visual maps

---

## 🌐 Collaboration

This project is part of a research collaboration between:

* **MachVis Lab, NUST**
* **NARC — National Agricultural Research Centre, Pakistan**
* **DAAD — German Academic Exchange Service**

---

## 📄 Publication & Links

* Final Report (Website) — *Coming Soon*
* Poster — *Available Soon*
* Publication — **WIP**

---

## 📬 Contact

For questions, collaborations, or dataset access:

Muhammad Umer Khan
Shalina Riaz
Syed Hashir Ahmad Kazmi

Contact
mukhan.bscs21seecs@seecs.edu.pk
MachVis Lab, NUST

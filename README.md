# EleGANt: Exquisite and Locally Editable GAN for Makeup Transfer

[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

Official [PyTorch](https://pytorch.org/) implementation of ECCV 2022 paper "[EleGANt: Exquisite and Locally Editable GAN for Makeup Transfer](https://arxiv.org/abs/2207.09840)"

*Chenyu Yang, Wanrong He, Yingqing Xu, and Yang Gao*.

![teaser](assets/figs/teaser.png)

## Getting Started

- [Installation](assets/docs/install.md)
- [Prepare Dataset & Checkpoints](assets/docs/prepare.md)

## Test

To test our model, download the [weights](https://drive.google.com/drive/folders/1xzIS3Dfmsssxkk9OhhAS4svrZSPfQYRe?usp=sharing) of the trained model and run

```bash
python scripts/demo.py
```

Examples of makeup transfer results can be seen [here](assets/images/examples/).

## Train

To train a model from scratch, run

```bash
python scripts/train.py
```

## Multi-Face Processing

EleGANt now supports processing multiple faces in a single image. All detected faces will automatically receive the same makeup transfer.

**Usage:**
- All entry points (demo.py, API, Streamlit) automatically detect and process multiple faces
- No configuration needed - works out of the box for images with 1+ faces

**Known Limitations:**
- Overlapping faces may have blending artifacts due to direct pixel assignment
- Reference images with multiple faces: only first face's makeup is used
- Faces processed sequentially (~3-5s per face on CPU, ~0.5-1s per face on GPU)
- No face quality filtering - all detected faces are processed
- Intensity controls (API/Streamlit) currently non-functional with multi-face images

**Recommended Use Cases:**
- Group photos (2-5 faces)
- Portrait photography
- Family photos
- Product demos with multiple models

**Not Recommended:**
- Very large group photos (10+ faces) - may be slow or run out of memory
- Images with significant face overlap - visual artifacts may occur

## Customized Transfer

https://user-images.githubusercontent.com/61506577/180593092-ccadddff-76be-4b7b-921e-0d3b4cc27d9b.mp4

This is our demo of customized makeup editing. The interactive system is built upon [Streamlit](https://github.com/streamlit/streamlit) and the interface in `./training/inference.py`.

**Controllable makeup transfer.**

![control](assets/figs/control.png 'controllable makeup transfer')

**Local makeup editing.**

![edit](assets/figs/edit.png 'local makeup editing')

## Citation

If this work is helpful for your research, please consider citing the following BibTeX entry.

```text
@article{yang2022elegant,
  title={EleGANt: Exquisite and Locally Editable GAN for Makeup Transfer},
  author={Yang, Chenyu and He, Wanrong and Xu, Yingqing and Gao, Yang}
  journal={arXiv preprint arXiv:2207.09840},
  year={2022}
}
```

## Acknowledgement

Some of the codes are build upon [PSGAN](https://github.com/wtjiang98/PSGAN) and [aster.Pytorch](https://github.com/ayumiymk/aster.pytorch).

## License

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

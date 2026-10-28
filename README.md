# Eliksiro Sans

## 简览 | At a Glance

Eliksiro Sans是一款集成了械黑与一定IBM Plex Sans补充并修复少量既有问题的字体。本仓库为以Python实现的字体构建流程。

Eliksiro Sans is a typeface that combines Frex Sans (械黑) with supplementary characters from IBM Plex Sans, and fixes a few existing issues. This repository contains its build pipeline, implemented in Python.

## 构建 | Build

需要[uv](https://docs.astral.sh/uv/)和git。

Requires [uv](https://docs.astral.sh/uv/) and git.

```bash
uv run eliksiro-sans fetch
uv run eliksiro-sans merge
uv run eliksiro-sans build
uv run eliksiro-sans verify
```

`fetch`把上游源文件取到`upstream/`（约1.1 GB），并核对内容与预期一致。`merge`把IBM Plex Sans SC的补充字形并进械黑三个母版的副本，改用Eliksiro Sans的名称和度量，写到`work/merged/`（约3分钟，需要约4 GB内存）。`build`把它们编译成CFF2可变字体`out/EliksiroSans-VF.otf`，并附上`OFL.txt`和`FONTLOG.txt`（约3分钟）。同样的源文件总是编出逐字节相同的字体。`verify`把编译结果与上游字体比对：械黑部分对照官方字体，补充层在8个字重上对照IBM的静态字体，并检查全部字形的插值（约3.5分钟）。

`fetch` fetches the upstream sources into `upstream/` (about 1.1 GB) and checks that their contents are exactly as expected. `merge` adds the IBM Plex Sans SC supplement to copies of the three Frex Sans masters, with Eliksiro Sans's names and metrics, in `work/merged/` (about 3 minutes, using about 4 GB of memory). `build` compiles them into the CFF2 variable font `out/EliksiroSans-VF.otf`, next to `OFL.txt` and `FONTLOG.txt` (about 3 minutes). The same sources always give a byte-identical font. `verify` checks the built font against the upstream fonts: the Frex Sans part against the official font, the supplement against IBM's static fonts at eight weights, and the interpolation of every glyph (about 3.5 minutes).

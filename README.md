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
```

`fetch`把上游源文件取到`upstream/`（约1.1 GB），并核对内容与预期一致。`merge`把IBM Plex Sans SC的补充字形并进械黑三个母版的副本，写到`work/merged/`（约3分钟，需要约4 GB内存）。字体本身的编译还没有实现。

`fetch` fetches the upstream sources into `upstream/` (about 1.1 GB) and checks that their contents are exactly as expected. `merge` adds the IBM Plex Sans SC supplement to copies of the three Frex Sans masters in `work/merged/` (about 3 minutes, using about 4 GB of memory). Compiling the font itself is not implemented yet.

# Eliksiro Sans

## 简览 | At a Glance

Eliksiro Sans是一款集成了械黑与一定IBM Plex Sans补充并修复少量既有问题的字体。本仓库为以Python实现的字体构建流程。

Eliksiro Sans is a typeface that combines Frex Sans (械黑) with supplementary characters from IBM Plex Sans, and fixes a few existing issues. This repository contains its build pipeline, implemented in Python.

## 构建 | Build

需要[uv](https://docs.astral.sh/uv/)和git。

Requires [uv](https://docs.astral.sh/uv/) and git.

```bash
uv run eliksiro-sans fetch
```

`fetch`把上游源文件取到`upstream/`（约1.1 GB），并核对内容与预期一致。字体本身的构建还没有实现。

`fetch` fetches the upstream sources into `upstream/` (about 1.1 GB) and checks that their contents are exactly as expected. Building the font itself is not implemented yet.

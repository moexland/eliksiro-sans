# Eliksiro Sans

Eliksiro Sans是一款集成了械黑GB与一定IBM Plex Sans SC补充并修复少量既有问题的字体。本包是它的网页版：字体按字频切成许多WOFF2切片，配有CSS入口，浏览器只下载页面用到的切片。

Eliksiro Sans is a typeface that combines Frex Sans GB (械黑GB) with supplementary characters from IBM Plex Sans SC, and fixes a few existing issues. This package is its web version: the font is sliced by character frequency into many WOFF2 files, with a CSS entry, so that browsers download only the slices a page uses.

## 用法 | Usage

```bash
npm install @moexland/eliksiro-sans
```

```css
@import "@moexland/eliksiro-sans";

body {
  font-family: "Eliksiro Sans", sans-serif;
}
```

- 字重为100至700的可变字重，`font-weight`取其间任意值均可。
- 拉丁字母、标点与全角字符都在同一片里，字距调整、标点挤压等排版功能在它们之间照常生效。
- 完整的OTF字体可从`@moexland/eliksiro-sans/otf`取得。

<!-- 分开中英两个列表 | keeps the two lists apart -->

- The weight is variable from 100 to 700; any `font-weight` in between works.
- Latin letters, punctuation and full-width forms share one slice, so kerning, punctuation squeezing and other layout features work between them.
- The full OTF font is at `@moexland/eliksiro-sans/otf`.

## 授权 | License

字体以SIL开源字体授权1.1版发布，见`OFL.txt`。切片以Google Fonts的简体中文切片表（Apache-2.0）为底。源代码与更多介绍见[GitHub](https://github.com/moexland/eliksiro-sans)。

The font is licensed under the SIL Open Font License, Version 1.1; see `OFL.txt`. The slices start from Google Fonts' Simplified Chinese slices (Apache-2.0). For the source and more, see [GitHub](https://github.com/moexland/eliksiro-sans).

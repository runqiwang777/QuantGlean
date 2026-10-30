# QuantGlean website demo

Live URL: https://runqiwang777.github.io/QuantGlean/

This buildless, browser-local walkthrough uses the repository's reviewed AQR example. It supports English/Chinese, focus and depth selection, evidence links, and Markdown export. It uses curated content and does not accept uploaded PDFs, call an AI API, or execute a backtest.

## Preview

From the repository root, run:

```sh
node scripts/build-demo.mjs
python -m http.server 8765 --directory _site
```

Open http://localhost:8765/. The build copies `site/` and the existing poster into ignored `_site/`; source assets are not duplicated in Git.

## Publish and maintain

The `pages.yml` workflow builds and publishes the static site on relevant pushes to `main`, or manual dispatch. GitHub Pages must use GitHub Actions as its publishing source. The deployment contains only `_site/`.

Edit `app.js` for bilingual walkthrough text, `styles.css` for presentation, and `index.html` for structure. Keep evidence locators and hypothesis status aligned with `examples/aqr-century-trend-following/`. The website is an abbreviated walkthrough; the repository note remains the complete example.

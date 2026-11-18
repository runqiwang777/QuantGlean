# Contributing to QuantGlean

Thanks for your interest in improving QuantGlean. This guide covers the repository layout, how to preview the demo site locally, and what to check before opening a pull request.

QuantGlean is a research skill and analysis workflow. It is not a trading system or investment advice, so contributions should keep that framing (see the [disclaimer in the README](README.md#disclaimer)).

## Repository structure

| Path | Purpose |
| --- | --- |
| [`SKILL.md`](SKILL.md) | The skill: analysis instructions for reading a quantitative research report. Translations: [`SKILL_CN.md`](SKILL_CN.md), [`SKILL_JA.md`](SKILL_JA.md), [`SKILL_KO.md`](SKILL_KO.md). |
| [`README.md`](README.md) | Project overview. Translations: [`README_CN.md`](README_CN.md), [`README_JA.md`](README_JA.md), [`README_KO.md`](README_KO.md). |
| [`templates/`](templates/) | The reusable Alpha Hypothesis Card ([`alpha-hypothesis.md`](templates/alpha-hypothesis.md)) and its Chinese, Japanese, and Korean versions. |
| [`examples/aqr-century-trend-following/`](examples/aqr-century-trend-following/) | The reviewed worked example: [`README.md`](examples/aqr-century-trend-following/README.md), [`README_CN.md`](examples/aqr-century-trend-following/README_CN.md), and [`SOURCE.md`](examples/aqr-century-trend-following/SOURCE.md) (source version and evidence map). |
| [`site/`](site/) | Source of the buildless interactive demo: `index.html`, `app.js`, `locales.js`, `styles.css`, and [`README.md`](site/README.md). |
| [`scripts/`](scripts/) | [`build-demo.mjs`](scripts/build-demo.mjs) builds the demo into `_site/`; [`demo-build.test.mjs`](scripts/demo-build.test.mjs) is its smoke test. |
| [`assets/`](assets/) | The poster image `QuantGlean.png`, used by the README and the demo. |
| [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | Workflow that tests, builds, and publishes the demo to GitHub Pages. |
| `_site/` | Generated build output. It is listed in [`.gitignore`](.gitignore); do not commit it. |

## Preview the demo locally

The demo needs Node.js and Python. From the repository root, run the commands from [`site/README.md`](site/README.md):

```sh
node scripts/build-demo.mjs
python -m http.server 8765 --directory _site
```

Then open <http://localhost:8765/>.

The build copies `site/` and the existing poster into the ignored `_site/` directory. Re-run `node scripts/build-demo.mjs` after editing files in `site/`.

Language deep links: `?lang=en`, `?lang=zh`, `?lang=ja`, `?lang=ko`.

The live demo is at <https://runqiwang777.github.io/QuantGlean/>. See [`site/README.md`](site/README.md) for which file controls what (`app.js`, `locales.js`, `styles.css`, `index.html`).

## Contribution guidelines

- **Fork, branch, and open a pull request** against `main`. Keep each pull request focused on one change, and reference the issue it addresses.
- **Keep content grounded in sources.** Do not fabricate metrics, citations, assumptions, or validation results ([`SKILL.md`](SKILL.md)). Following the [template](templates/alpha-hypothesis.md), fill unknown fields with `Unknown` and mark unexecuted validation as `Not run`.
- **Keep the example and demo aligned.** Keep evidence locators and hypothesis status on the website aligned with [`examples/aqr-century-trend-following/`](examples/aqr-century-trend-following/). The website is an abbreviated walkthrough; the repository note remains the complete example.
- **Check translations.** `README`, `SKILL`, and the hypothesis template exist in English, Chinese, Japanese, and Korean; the worked example is in English and Chinese. If you change one version, check whether its counterparts need the same change, or say in the pull request that they do.
- **Do not commit generated output** (`_site/`).
- **License:** the project is released under the [MIT License](LICENSE).

## Before opening a pull request

1. Run the smoke test, the same command the Pages workflow runs before deploying:

   ```sh
   node --test scripts/demo-build.test.mjs
   ```

   It rebuilds `_site/` and checks that `index.html`, `app.js`, `styles.css`, `locales.js`, `assets/QuantGlean.png`, and `.nojekyll` are present.

2. If you changed `site/` or `scripts/`, preview the demo using the [steps above](#preview-the-demo-locally) and check the affected pages and languages.
3. If you changed Markdown, check that relative links and anchors still resolve.

Note: [`pages.yml`](.github/workflows/pages.yml) runs on pushes to `main` (for changes under `site/`, the two scripts, `assets/QuantGlean.png`, or the workflow itself) and on manual dispatch. It does not run on pull requests, so run the checks above locally.

## Existing documentation

- [README](README.md) ([简体中文](README_CN.md) · [日本語](README_JA.md) · [한국어](README_KO.md))
- [Skill instructions](SKILL.md)
- [Alpha Hypothesis Card template](templates/alpha-hypothesis.md)
- [Worked example](examples/aqr-century-trend-following/README.md) and its [source and evidence map](examples/aqr-century-trend-following/SOURCE.md)
- [Demo site notes](site/README.md)
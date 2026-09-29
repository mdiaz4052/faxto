# FaXto / release-led pilot / 29 September 2026

## Approval boundary

This is a preview, not a production deployment. The starting main commit is
`f4b0f375a474a30e0e64872431ba650dee9f79a3`. Work is isolated on
`pilot/release-led-2026-09-29`. Do not merge or deploy without Miguel's review.
CNAME, Pages settings, main, and existing deployment configuration are untouched.
The added CI has read-only repository permissions and no deployment step.

The preview is public, as is this repository. No credentials, private listening
history, or unreleased material are included. Catalog API account/library flags
were deliberately excluded from the metadata receipt.

## What this pilot changes

- A release-led homepage: intact cover art, a clear listening action, a browsable
  2-album / 5-single catalog with progressive filters, then the artistic statement.
- SACRILEGIUM and NOS CREEMOS ALGO as digital liner notes: prominent listening,
  native lyric disclosures, shareable song anchors, original stories, navigation.
- A compact mobile menu; all primary content also works without JavaScript.
- The approved dense rainbow particle field, now separate from the featured cover,
  with pause, keyboard modes, horizontal swipe, reduced-motion support, and no
  continuous redraw while paused or offscreen. No central letter or sphere.
- Only one disclosure link per pilot page: “made with Suno AI”.
- The supplied LANDR link for Nos Creemos Algo replaces its old generic Links target.
- Local fonts already present in this repository; no new third-party font runtime.

The other five release HTML files, links.html, disclosure.html, original styles,
original scripts and artwork bytes are unchanged. Their old design remains visible
when a visitor leaves a pilot page. This is intentional bounded pilot scope.

## Branding is replaceable

`css/brand.css` is the provisional palette/type layer, separate from page layout.
`content/site.json` has optional `brand.wordmark` and `brand.symbol` paths. Set them
only after the commissioned assets are approved. A wordmark replaces the text;
a symbol is optional. The header and footer accommodate the assets without
changing release data. The field is an independent module and can be removed or
replaced. No permanent logo has been invented.

## Content and future short-prompt updates

`content/releases.json` is the catalog source. The pilot pages use shared templates
in `templates/`; the remaining pages are marked `legacy` and are not overwritten.
`featured` and `secondary_featured` in site.json are editorial decisions, not the
most recently discovered store listing. Importing a new release never promotes it
or replaces any approved lyrics or story automatically.

`tools/import_release.py` prepares a review-only candidate from a supplied LANDR
link and optional structured catalog metadata. It validates artist/title and full
track count when metadata is available, rejects incomplete pagination and unsafe
source URLs, and never downloads art or writes into the live catalog. Public HTML
metadata/store links are retained only as unverified candidates. LANDR's changing
markup is not claimed to be a universal, production-qualified API.

An actual Apple Music catalog lookup for Nos Creemos Algo returned album
6800922335, one track (6800922336), UPC 991048761872 and ISRC CAGOO2664363. A minimal
public-metadata receipt is in `content/imports/nos-creemos-algo.json`. The title,
artist and complete one-track structure agree with the existing release. The
search also returned unrelated artists, which were excluded. The result did not
include the matching artist-profile ID; this limitation is recorded. The current
page retains its already approved local artwork, lyrics, and story. The artist's
LANDR URL is authoritative for the changed listening button; no guessed store
links or externally inferred interpretation are published.

The initial web check could not retrieve the LANDR promo page. This does not mean
the supplied link is invalid. Live LANDR-only extraction is not represented as
successfully qualified. A future prompt can supply only the LANDR link; the
assistant can retrieve complementary official metadata as needed, then prepare
and review a candidate. Ambiguous identity/edition or missing source data remains
an explicit review gate, not a fabricated release page.

Example bounded dry run (writes only a new candidate):

```sh
python3 tools/import_release.py \
  --landr-url https://release.landr.com/nos-creemos-algo \
  --artist FaXto --title 'Nos Creemos Algo' --slug nos-creemos-algo \
  --metadata content/imports/nos-creemos-algo.json --offline \
  --out /tmp/nos-creemos-algo-review.json
```

## Rebuild and test

```sh
python3 tools/build_site.py
python3 tools/build_site.py --check
python3 -m unittest discover -s tests -v
python3 -m pip install -r requirements-browser.txt
python3 -m playwright install chromium
python3 tools/browser_check.py --out qa/browser
```

HTML generation and the 24 unit checks require only Python's standard library.
Browser checks cover 320, 390, 768, 1024, 1440 and 1920 pixel widths for all three
pilot pages, image loading/framing, overflow, menu behavior, catalog filters,
lyric fragments, animation controls, reduced motion and no-JavaScript operation.
Local rendering used the `--memory` mode because this runtime disallows browser
network/file navigation; it inlines the same local assets only for that test.
CI uses ordinary local HTTP and preserves its separate report and screenshots.
It also probes the exact-commit raw.githack preview and compares returned HTML,
CSS, JS and featured image bytes; availability is reported separately.

Unit checks enforce original artwork hashes, verbatim lyric text, unchanged
approved editorial hashes, unchanged legacy pages, internal links, unique IDs,
HTTPS outbound links, noindex on the preview, and a single disclosure entry.
This is not a Safari/iOS-device certification or a formal accessibility audit.

## Publication, only after separate approval

The generated pilot HTML is intentionally noindex and carries a preview banner.
Before an approved production merge, set `preview` to false in site.json, rebuild,
update preview-specific tests intentionally, review the final diff and preview,
then merge only with explicit authorization. Do not change DNS or hosting as a
side effect. An abandoned pilot requires no production rollback: main stays as it
was. The preview URL is pinned to an immutable commit rather than a moving branch.

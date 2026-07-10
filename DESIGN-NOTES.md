# FaXto provisional redesign — “Void Cathedral”

## Purpose

This branch tests whether FaXto should evolve from a restrained liner-note archive into a more immersive artist site. It deliberately preserves the existing philosophical voice while substantially changing hierarchy, scale, navigation, motion, and catalog presentation.

## Design thesis

- **The void is spatial, not merely black.** Orbital geometry and instrument-like metadata turn emptiness into an active environment.
- **The sacred is structural, not ornamental.** The redesign reduces faux-ecclesiastical decoration and instead uses procession, scale, repetition, thresholds, and ritual numbering.
- **The work comes first.** SACRILEGIUM is visible above the fold; full albums become large visual chambers; singles become compact transmissions.
- **The method belongs in the art.** AI disclosure is elevated from footer fine print to a major section framing the machine as instrument and human curation as authorship.
- **Motion is restrained and optional.** CSS orbits, reveal transitions, and pointer parallax support atmosphere while respecting reduced-motion preferences.

## Scope

Changed: homepage structure, global design tokens, homepage CSS, release-page CSS, disclosure-page CSS, reveal/navigation script, favicon.

Not changed: release copy, lyrics, album art, LANDR destinations, or the underlying static-site architecture.

## Review questions

1. Does the larger, more kinetic presentation feel more like FaXto—or does it overpower the intimacy of the writing?
2. Should the orange “signal” accent replace the current tarnished-gold accent, or should the palette remain more ecclesiastical?
3. Should album pages receive their own visual identity per release, rather than sharing one template?
4. Should the homepage eventually include embedded playback previews, or remain intentionally external-link-only?

# Bureaubot models

Eight original heads and a gear/clipboard department emblem, fitted to the
original Toontown Cog A/B/C bodies. Each full-body BAM includes the body's
skeleton, attached head, medallion and embedded textures. The head BAMs and
emblem are also supplied separately for reuse.

The editable source is `toontown/suit/BureaubotModels.py`. The game builds its
gallery actors from this source and binds the existing neutral/walk animations;
the exported BAMs are reviewable model assets, not networked battle enemies.
Animation clips remain in the normal resources checkout. Full-body exports
contain the posed rig, not embedded animation clips.

Regenerate all exports and the model sheet from the repository root:

```sh
python tools/preview_bureaubots.py --export assets/bureaubots/models
```

Preview the actual five-row gallery with local avatar/OTP adapters:

```sh
python tools/preview_cog_gallery.py
```

In the game, open the Shtickerbook's Cog Gallery and click a Bureaubot portrait
or its department emblem. The model viewer supports previous/next, turning,
and close. All original 32 Cog records, quotas, summons and four radar tracks
remain on their existing indices; the eight new gallery entries are a separate
display catalog and do not invent defeat progress.

# Media assets

Twelve slot assets plus the share card. Each file's slot id, path and real pixel
size are listed in `../../lib/media.ts`, which is what `<MediaSlot>` reads: a
slot id present there renders its file, one that is absent renders the designed
placeholder. Both occupy the same box, so adding or removing a file never moves
the layout.

To replace one, keep the filename and the aspect ratio and update the `width` /
`height` in `lib/media.ts` if the pixel size changes. To add a new slot, add the
`<MediaSlot>` call first, then the file, then the manifest row.

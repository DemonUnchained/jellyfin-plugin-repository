# DemonUnchained Jellyfin Plugins

This repository publishes the Jellyfin plugin catalog for:

- [Trailer Reel](https://github.com/DemonUnchained/jellyfin-plugin-trailer-reel)
- [Theme Music Finder](https://github.com/DemonUnchained/jellyfin-plugin-theme-music-finder)

Add this URL in **Jellyfin Dashboard → Plugins → Repositories**:

```text
https://raw.githubusercontent.com/DemonUnchained/jellyfin-plugin-repository/main/manifest.json
```

`manifest.json` is regenerated automatically from public GitHub Releases. Each
release ZIP is downloaded during synchronization so its Jellyfin-required MD5
checksum is calculated from the actual published bytes.

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

Theme Music Finder 1.2.2.2 is available for Jellyfin 12.4 (`targetAbi=12.4.0.0`).
Version 1.2.1.9 remains available for Jellyfin 12.1 (`targetAbi=12.1.0.0`), with
its existing URL and checksum preserved.

Automatic discovery writes remain disabled by default
(`EnableAutomaticDiscoveryWrites=false`). The read-only audit can be reviewed
before enabling newly discovered audio installations; metadata scores do not
prove that a recording is the correct theme.

Prereleases are excluded unless their numeric version is explicitly listed in
that plugin's `allowedPrereleaseVersions`. Only Theme Music Finder 1.2.2.2 is
allowlisted, with a per-version ABI override. Other previews remain excluded,
and the GitHub release retains its prerelease status.

Run the offline catalog regression tests with:

```bash
python3 -m unittest discover -s tests -v
```

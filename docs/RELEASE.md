# Release process

## Prerequisites

- Push access to the GitHub repository
- GitHub Actions enabled with **Workflow permissions → Read and write** for releases

## Cut a release

1. Ensure `main` is up to date and all tests pass:

   ```bash
   pytest -q
   ```

2. Update the version in these files if bumping beyond `0.1.0`:
   - `pyproject.toml` (`version`)
   - `packaging/windows/Kotline.iss` (`MyAppVersion`)
   - `scripts/build_appimage.sh` (`VERSION`)

3. Commit and push to `main`.

4. Create and push a version tag (triggers [`.github/workflows/release.yml`](../.github/workflows/release.yml)):

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. Wait for the **Release** workflow to finish on GitHub Actions.

6. Verify artifacts on the [Releases](https://github.com/barad21/Kotline/releases) page:
   - `Kotline-Setup-0.1.0.exe` (Windows installer)
   - `Kotline-x86_64.AppImage` (Linux portable)
   - `kotline-linux-x86_64.tar.gz` (Linux folder bundle)

## Manual builds (without CI)

**Windows:**

```powershell
.\scripts\build_windows_installer.ps1
```

**Linux:**

```bash
./scripts/build_appimage.sh
tar -czf dist/kotline-linux-x86_64.tar.gz -C dist Kotline
```

## Smoke test checklist

- [ ] Windows installer completes and Start Menu shortcut launches Kotline
- [ ] AppImage launches on Linux (`chmod +x` first)
- [ ] **Load Demo** works in packaged builds (config + DXF resolve correctly)
- [ ] Open/save `.kesit` project files works

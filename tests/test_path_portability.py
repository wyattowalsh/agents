from wagents.repo_paths import migrate_absolute_path, render_portable_path, resolve_portable_path


def test_render_and_resolve_repo_root_token(tmp_path):
    repo = tmp_path / "agents"
    repo.mkdir()
    target = repo / "config" / "mcp-registry.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")
    portable = render_portable_path(target, repo_root=repo)
    assert portable == "${REPO_ROOT}/config/mcp-registry.json"
    assert resolve_portable_path(portable, repo_root=repo) == str(target.resolve())


def test_migrate_absolute_to_portable(tmp_path, monkeypatch):
    repo = tmp_path / "agents"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    raw = str((repo / "config/sync-manifest.json").resolve())
    assert migrate_absolute_path(raw, repo_root=repo, home=home).startswith("${REPO_ROOT}/")

"""Evita atualização remota divergente e upload de pacote alterado."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from scripts.publicar_space import publish


def bundle(tmp_path):
    (tmp_path / "app.py").write_text("# fixture")
    digest = hashlib.sha256((tmp_path / "app.py").read_bytes()).hexdigest()
    (tmp_path / "bundle-manifest.json").write_text(json.dumps({"app.py": digest}))
    return tmp_path


class FakeApi:
    def __init__(self, revision="expected"):
        self.revision = revision
        self.uploaded = None

    def whoami(self):
        return {"name": "owner"}

    def repo_exists(self, *args, **kwargs):
        return True

    def space_info(self, *args):
        return SimpleNamespace(sha=self.revision)

    def get_space_runtime(self, *args):
        return SimpleNamespace(requested_hardware="zero-a10g", hardware=None, stage="BUILDING")

    def upload_folder(self, **kwargs):
        self.uploaded = kwargs
        return SimpleNamespace(oid="new")


def test_publication_refuses_untracked_bundle_files_before_api(tmp_path, monkeypatch):
    path = bundle(tmp_path)
    (path / "unexpected.env").write_text("fixture")
    monkeypatch.setattr("scripts.publicar_space.HfApi", lambda: pytest.fail("API não deveria ser consultada"))
    with pytest.raises(ValueError):
        publish(path, "owner/project")


def test_update_refuses_changed_remote_and_existing_space_without_revision(tmp_path, monkeypatch):
    path = bundle(tmp_path)
    api = FakeApi("changed")
    monkeypatch.setattr("scripts.publicar_space.HfApi", lambda: api)
    with pytest.raises(FileExistsError):
        publish(path, "owner/project")
    with pytest.raises(ValueError):
        publish(path, "owner/project", "expected")
    assert api.uploaded is None


def test_update_is_bound_to_inspected_revision_and_free_hardware(tmp_path, monkeypatch):
    path = bundle(tmp_path)
    api = FakeApi()
    monkeypatch.setattr("scripts.publicar_space.HfApi", lambda: api)
    result = publish(path, "owner/project", "expected")
    assert api.uploaded["parent_commit"] == "expected"
    assert result["paid_hardware_requested"] is False

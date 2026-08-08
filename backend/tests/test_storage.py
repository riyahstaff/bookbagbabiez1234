import pytest

from app.storage.local import LocalStorageBackend


def test_save_then_read_round_trips_bytes(tmp_path):
    storage = LocalStorageBackend(tmp_path)
    storage.save("a/b/c.bin", b"hello world")
    assert storage.read("a/b/c.bin") == b"hello world"


def test_read_missing_file_raises(tmp_path):
    storage = LocalStorageBackend(tmp_path)
    with pytest.raises(FileNotFoundError):
        storage.read("nope.bin")


def test_exists_and_delete(tmp_path):
    storage = LocalStorageBackend(tmp_path)
    storage.save("x.bin", b"data")
    assert storage.exists("x.bin")
    storage.delete("x.bin")
    assert not storage.exists("x.bin")


def test_delete_missing_file_is_a_noop(tmp_path):
    storage = LocalStorageBackend(tmp_path)
    storage.delete("does-not-exist.bin")  # must not raise

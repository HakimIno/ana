from modules.storage.file_manager import FileManager

class TestFileManager:
    """Tests for FileManager storage operations."""

    def test_save_and_get_file(self, tmp_path):
        fm = FileManager(storage_dir=tmp_path)
        content = b"test content"
        filename = "test.txt"
        
        saved_path = fm.save_file(content, filename)
        assert saved_path.exists()
        assert fm.get_file_path(filename) == saved_path
        
        with open(saved_path, "rb") as f:
            assert f.read() == content

    def test_list_files(self, tmp_path):
        fm = FileManager(storage_dir=tmp_path)
        fm.save_file(b"1", "f1.txt")
        fm.save_file(b"22", "f2.txt")
        
        files = fm.list_files()
        assert len(files) == 2
        filenames = [f["filename"] for f in files]
        assert "f1.txt" in filenames
        assert "f2.txt" in filenames

    def test_delete_file(self, tmp_path):
        fm = FileManager(storage_dir=tmp_path)
        fm.save_file(b"data", "delete_me.txt")
        assert fm.delete_file("delete_me.txt") is True
        assert not (tmp_path / "delete_me.txt").exists()

    def test_delete_non_existent(self, tmp_path):
        fm = FileManager(storage_dir=tmp_path)
        assert fm.delete_file("nothing.txt") is False

    def test_cleanup(self, tmp_path):
        fm = FileManager(storage_dir=tmp_path)
        fm.save_file(b"1", "1.txt")
        fm.cleanup()
        assert tmp_path.exists()
        assert len(list(tmp_path.iterdir())) == 0

"""Tests for path traversal prevention."""
import pytest
import tempfile
from pathlib import Path
from app.utils.path_security import validate_safe_path, sanitize_filename, is_safe_path


class TestPathTraversalPrevention:
    """Test path traversal prevention utilities."""

    def test_validate_safe_path_normal(self):
        """Test normal safe path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Normal filename should work
            safe_path = validate_safe_path("test.txt", base_dir)
            assert safe_path.parent == base_dir
            assert safe_path.name == "test.txt"

    def test_validate_safe_path_traversal_attack(self):
        """Test path traversal attack prevention."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Path traversal attempts should fail
            traversal_attempts = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "../../../../root/.ssh/id_rsa",
                "../config.py",
                "../../secrets.env"
            ]

            for attack_path in traversal_attempts:
                with pytest.raises(ValueError, match="Path traversal attempt detected"):
                    validate_safe_path(attack_path, base_dir)

    def test_sanitize_filename_normal(self):
        """Test normal filename sanitization."""
        test_cases = [
            ("document.pdf", "document.pdf"),
            ("my file.txt", "my file.txt"),
            ("report_2024.xlsx", "report_2024.xlsx")
        ]

        for input_name, expected in test_cases:
            result = sanitize_filename(input_name)
            assert result == expected

    def test_sanitize_filename_dangerous(self):
        """Test dangerous filename sanitization."""
        dangerous_cases = [
            ("../../../etc/passwd", "___etc_passwd"),
            ("..\\..\\config.ini", "____config.ini"),
            ("file|with|pipes.txt", "file_with_pipes.txt"),
            ("file:with:colons.txt", "file_with_colons.txt"),
            ("file<with>brackets.txt", "file_with_brackets.txt"),
            ("file\"with\"quotes.txt", "file_with_quotes.txt"),
            ("file*with*wildcards.txt", "file_with_wildcards.txt"),
            ("file?with?questions.txt", "file_with_questions.txt")
        ]

        for dangerous_name, expected in dangerous_cases:
            result = sanitize_filename(dangerous_name)
            assert result == expected
            # Ensure no dangerous characters remain
            assert "../" not in result
            assert "..\\" not in result
            assert "|" not in result
            assert ":" not in result
            assert "*" not in result
            assert "?" not in result
            assert '"' not in result
            assert "<" not in result
            assert ">" not in result

    def test_sanitize_filename_edge_cases(self):
        """Test edge cases in filename sanitization."""
        # Empty filename
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            sanitize_filename("")

        # Filename that becomes empty after sanitization
        with pytest.raises(ValueError, match="Filename becomes empty after sanitization"):
            sanitize_filename("../../../")

        # Very long filename
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_is_safe_path_allowed(self):
        """Test safe path checking with allowed directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            allowed_dirs = [str(base_dir)]

            # Create a test file in allowed directory
            test_file = base_dir / "test.txt"
            test_file.write_text("test")

            # Should be safe
            assert is_safe_path(test_file, allowed_dirs) is True

    def test_is_safe_path_not_allowed(self):
        """Test safe path checking with disallowed paths."""
        with tempfile.TemporaryDirectory() as temp_dir1:
            with tempfile.TemporaryDirectory() as temp_dir2:
                base_dir = Path(temp_dir1)
                other_dir = Path(temp_dir2)
                allowed_dirs = [str(base_dir)]

                # Create a test file in non - allowed directory
                test_file = other_dir / "test.txt"
                test_file.write_text("test")

                # Should not be safe
                assert is_safe_path(test_file, allowed_dirs) is False

    def test_path_traversal_with_symlinks(self):
        """Test path traversal prevention with symbolic links."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Create a directory outside base
            outside_dir = Path(temp_dir).parent / "outside"
            outside_dir.mkdir(exist_ok=True)

            try:
                # Create symlink pointing outside
                symlink_path = base_dir / "evil_link"
                symlink_path.symlink_to(outside_dir)

                # Should detect this as unsafe
                allowed_dirs = [str(base_dir)]
                assert is_safe_path(symlink_path, allowed_dirs) is False

            except OSError:
                # Skip if symlinks not supported
                pytest.skip("Symbolic links not supported on this system")
            finally:
                # Cleanup
                if outside_dir.exists():
                    outside_dir.rmdir()

    def test_null_byte_injection(self):
        """Test null byte injection prevention."""
        malicious_names = [
            "test.txt\x00.exe",
            "document.pdf\x00malicious",
            "file\x00../../../etc/passwd"
        ]

        for malicious_name in malicious_names:
            result = sanitize_filename(malicious_name)
            assert "\x00" not in result
            assert result.replace("_", "").replace(".", "").isalnum()

    def test_unicode_normalization(self):
        """Test Unicode filename handling."""
        unicode_names = [
            "café.txt",
            "résumé.pdf",
            "naïve.doc",
            "文档.txt"
        ]

        for unicode_name in unicode_names:
            result = sanitize_filename(unicode_name)
            # Should preserve Unicode characters
            assert len(result) > 0
            # Should not contain dangerous characters
            assert "../" not in result

    def test_windows_reserved_names(self):
        """Test Windows reserved filename handling."""
        reserved_names = [
            "CON.txt",
            "PRN.pdf",
            "AUX.doc",
            "NUL.txt",
            "COM1.txt",
            "LPT1.txt"
        ]

        for reserved_name in reserved_names:
            result = sanitize_filename(reserved_name)
            # Should still be a valid filename
            assert len(result) > 0
            assert "." in result

    def test_path_case_sensitivity(self):
        """Test path validation with case sensitivity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            # Test case variations
            test_cases = [
                "Test.txt",
                "TEST.TXT",
                "test.TXT"
            ]

            for test_case in test_cases:
                safe_path = validate_safe_path(test_case, base_dir)
                assert safe_path.parent == base_dir

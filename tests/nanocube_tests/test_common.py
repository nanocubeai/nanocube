import unittest
from nanocube.common import pythonize


class TestPythonizeFunction(unittest.TestCase):

    def test_pythonize_with_default_lowered(self):
        self.assertEqual(pythonize("Hello World"), "Hello_World")

    def test_pythonize_with_lowered_set_to_true(self):
        self.assertEqual(pythonize("Hello World", lowered=True), "hello_world")

    def test_pythonize_with_single_word(self):
        self.assertEqual(pythonize("Hello"), "Hello")

    def test_pythonize_with_single_word_and_lowered_set_to_true(self):
        self.assertEqual(pythonize("Hello", lowered=True), "hello")

    def test_pythonize_with_special_characters(self):
        self.assertEqual(pythonize("Hello! World@#$"), "Hello_World")

    def test_pythonize_with_numbers(self):
        self.assertEqual(pythonize("Hello123 World456"), "Hello123_World456")

    def test_pythonize_with_underscores(self):
        self.assertEqual(pythonize("Hello_World"), "Hello_World")

    def test_pythonize_with_empty_string(self):
        self.assertEqual(pythonize(""), "")


if __name__ == '__main__':
    unittest.main()

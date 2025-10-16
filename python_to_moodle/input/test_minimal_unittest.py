"""
Tests pour test_minimal.py
"""

import unittest
from test_minimal import double


class TestDouble(unittest.TestCase):
    """Tests pour la fonction double"""

    def test_simple(self):
        """Test basique"""
        self.assertEqual(double(5), 10)

    def test_zero(self):
        """Test avec zéro"""
        self.assertEqual(double(0), 0)


if __name__ == '__main__':
    unittest.main()

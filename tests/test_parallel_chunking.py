"""
Tests for parallel account contact chunking.
Ensures contacts are divided evenly across multiple selected profiles.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestParallelChunking(unittest.TestCase):
    """Verifies that the data chunking math and range slicing behaves correctly."""

    def _chunk_contacts(self, contacts, num_bots):
        """Helper mirroring the chunking logic in automation_mixin.py"""
        if not contacts:
            return []
        if num_bots <= 0:
            return []
        chunk_size = (len(contacts) + num_bots - 1) // num_bots
        
        chunks = []
        for idx in range(num_bots):
            chunk = contacts[idx * chunk_size : (idx + 1) * chunk_size]
            chunks.append(chunk)
        return chunks

    def test_empty_contacts(self):
        """Verify behavior with empty contacts."""
        contacts = []
        chunks = self._chunk_contacts(contacts, 3)
        self.assertEqual(chunks, [])

    def test_fewer_contacts_than_profiles(self):
        """Verify chunking when contacts count is less than the number of profiles/bots."""
        contacts = [{"phone": "1"}, {"phone": "2"}]
        # 2 contacts, 4 bots.
        # chunk_size = (2 + 4 - 1) // 4 = 5 // 4 = 1.
        chunks = self._chunk_contacts(contacts, 4)
        
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0], [{"phone": "1"}])
        self.assertEqual(chunks[1], [{"phone": "2"}])
        self.assertEqual(chunks[2], [])
        self.assertEqual(chunks[3], [])

    def test_perfectly_divisible(self):
        """Verify chunking when contacts count is perfectly divisible by the number of profiles."""
        contacts = [{"phone": str(i)} for i in range(12)]
        chunks = self._chunk_contacts(contacts, 3)
        
        self.assertEqual(len(chunks), 3)
        # chunk_size = 12 // 3 = 4
        self.assertEqual(len(chunks[0]), 4)
        self.assertEqual(len(chunks[1]), 4)
        self.assertEqual(len(chunks[2]), 4)
        # Flat list matches original
        flat_list = [c for chunk in chunks for c in chunk]
        self.assertEqual(flat_list, contacts)

    def test_not_perfectly_divisible(self):
        """Verify chunking when contacts count is not perfectly divisible by profiles."""
        contacts = [{"phone": str(i)} for i in range(10)]
        chunks = self._chunk_contacts(contacts, 3)
        
        self.assertEqual(len(chunks), 3)
        # chunk_size = (10 + 3 - 1) // 3 = 4
        self.assertEqual(len(chunks[0]), 4)  # indices 0,1,2,3
        self.assertEqual(len(chunks[1]), 4)  # indices 4,5,6,7
        self.assertEqual(len(chunks[2]), 2)  # indices 8,9
        
        flat_list = [c for chunk in chunks for c in chunk]
        self.assertEqual(flat_list, contacts)

    def test_single_profile(self):
        """Verify chunking with only one profile."""
        contacts = [{"phone": str(i)} for i in range(5)]
        chunks = self._chunk_contacts(contacts, 1)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], contacts)


if __name__ == "__main__":
    unittest.main()

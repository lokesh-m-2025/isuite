import unittest
from src.utils import validate_record, transform_record

class TestETLUtils(unittest.TestCase):
    def test_validate_record_success(self):
        record = {
            'order_id': '123',
            'customer_id': '456',
            'order_date': '2023-10-01',
            'amount': '99.99'
        }
        validate_record(record)

    def test_validate_record_missing_field(self):
        record = {
            'order_id': '123',
            'customer_id': '456',
            'order_date': '2023-10-01'
        }
        with self.assertRaises(ValueError):
            validate_record(record)

    def test_validate_record_type_error(self):
        record = {
            'order_id': 'abc',
            'customer_id': '456',
            'order_date': '2023-10-01',
            'amount': '99.99'
        }
        with self.assertRaises(ValueError):
            validate_record(record)

    def test_transform_record(self):
        record = {
            'order_id': '123',
            'customer_id': '456',
            'order_date': '2023-10-01',
            'amount': '99.99'
        }
        transformed = transform_record(record)
        self.assertEqual(transformed['order_id'], 123)
        self.assertEqual(transformed['customer_id'], 456)
        self.assertEqual(transformed['amount'], 99.99)

if __name__ == '__main__':
    unittest.main()

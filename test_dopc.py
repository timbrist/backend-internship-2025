import unittest
from unittest.mock import patch
import json
from dopc import DOPC

class TestDOPC(unittest.TestCase):

    def setUp(self):
        self.dopc = DOPC()

    @patch('requests.get')
    def test_fetch_venue_data_success(self, mock_get):
        mock_get.side_effect = [
            unittest.mock.Mock(status_code=200, json=lambda: {'static_key': 'static_value'}),
            unittest.mock.Mock(status_code=200, json=lambda: {'dynamic_key': 'dynamic_value'})
        ]
        static_data, dynamic_data = self.dopc.fetch_venue_data("test_venue")
        self.assertEqual(static_data, {'static_key': 'static_value'})
        self.assertEqual(dynamic_data, {'dynamic_key': 'dynamic_value'})

    @patch('requests.get')
    def test_fetch_venue_data_failure(self, mock_get):
        mock_get.side_effect = [
            unittest.mock.Mock(status_code=404),
            unittest.mock.Mock(status_code=404)
        ]
        static_data, dynamic_data = self.dopc.fetch_venue_data("test_venue")
        self.assertIsNone(static_data)
        self.assertIsNone(dynamic_data)

    def test_get_small_order_surcharge(self):
        self.assertEqual(self.dopc.get_small_order_surcharge(1000, 800), 200)
        self.assertEqual(self.dopc.get_small_order_surcharge(1000, 1000), 0)
        self.assertEqual(self.dopc.get_small_order_surcharge(1000, 1200), 0)

    def test_get_delivery_distance(self):
        user_coords = (60.1699, 24.9384)  # Helsinki
        venue_coords = (60.192059, 24.945831)  # Another point in Helsinki
        distance = self.dopc.get_delivery_distance(user_coords, venue_coords)
        self.assertAlmostEqual(distance, 2444.5, delta=10)  # Approximate distance in meters

    def test_get_delivery_fee(self):
        delivery_pricing = {
            'base_price': 500,
            'distance_ranges': [
                {'min': 0, 'max': 2000, 'a': 100, 'b': 2},
                {'min': 2000, 'max': 5000, 'a': 200, 'b': 3},
                {'min': 5000, 'max': 0, 'a': 300, 'b': 4}  # max=0 indicates no upper limit
            ]
        }
        self.assertEqual(self.dopc.get_delivery_fee(1500, delivery_pricing), 530)
        self.assertEqual(self.dopc.get_delivery_fee(3000, delivery_pricing), 590)
        self.assertEqual(self.dopc.get_delivery_fee(7000, delivery_pricing), 800)
        self.assertIsNone(self.dopc.get_delivery_fee(9000, delivery_pricing))  # Out of range

    def test_get_total_price(self):
        self.assertEqual(self.dopc.get_total_price(1000, 500, 200), 1700)
        self.assertEqual(self.dopc.get_total_price(800, 600, 100), 1500)

    @patch.object(DOPC, 'fetch_venue_data')
    def test_get_delivery_order_price_success(self, mock_fetch):
        mock_fetch.return_value = (
            {
                'venue_raw': {
                    'location': {
                        'coordinates': [24.945831, 60.192059]  # Venue coords (lon, lat)
                    }
                }
            },
            {
                'venue_raw': {
                    'delivery_specs': {
                        'order_minimum_no_surcharge': 1000,
                        'delivery_pricing': {
                            'base_price': 500,
                            'distance_ranges': [
                                {'min': 0, 'max': 2000, 'a': 100, 'b': 2},
                                {'min': 2000, 'max': 0, 'a': 200, 'b': 3}
                            ]
                        }
                    }
                }
            }
        )

        response, status = self.dopc.get_delivery_order_price("test_venue", 800, 60.1699, 24.9384)
        self.assertEqual(status, 200)
        self.assertEqual(response["total_price"], 1230)  # 800 + 130 (surcharge) + 300 (fee)
        self.assertEqual(response["small_order_surcharge"], 200)

    @patch.object(DOPC, 'fetch_venue_data')
    def test_get_delivery_order_price_failure(self, mock_fetch):
        mock_fetch.return_value = (None, None)
        response, status = self.dopc.get_delivery_order_price("invalid_venue", 800, 60.1699, 24.9384)
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Venue data not found")

if __name__ == "__main__":
    unittest.main()

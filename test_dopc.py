import unittest
import requests

class TestDOPCHTTP(unittest.TestCase):

    BASE_URL = "http://localhost:8000/api/v1/delivery-order-price"

    def test_valid_request(self):
        params = {
            "venue_slug": "home-assignment-venue-helsinki",
            "cart_value": 1000,
            "user_lat": 60.17094,
            "user_lon": 24.93087
        }
        response = requests.get(self.BASE_URL, params=params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_price", data)
        self.assertIn("delivery", data)
        self.assertIn("small_order_surcharge", data)

    def test_invalid_venue_slug(self):
        params = {
            "venue_slug": "invalid-venue",
            "cart_value": 1000,
            "user_lat": 60.17094,
            "user_lon": 24.93087
        }
        response = requests.get(self.BASE_URL, params=params)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Venue data not found")

    def test_delivery_not_available(self):
        params = {
            "venue_slug": "home-assignment-venue-helsinki",
            "cart_value": 1000,
            "user_lat": 60.0,
            "user_lon": 0.0  # Far away location
        }
        response = requests.get(self.BASE_URL, params=params)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Delivery not available for this distance")

if __name__ == "__main__":
    unittest.main()

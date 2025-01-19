import requests
from math import radians, sin, cos, sqrt, atan2


class DOPC:
    def __init__(self,home_assignment_api = "https://consumer-api.development.dev.woltapi.com/home-assignment-api/v1/venues"):
        self.home_assignment_api = home_assignment_api

    def fetch_venue_data(self, venue_slug):
        static_url = f"{self.home_assignment_api}/{venue_slug}/static"
        dynamic_url = f"{self.home_assignment_api}/{venue_slug}/dynamic"
        static_response = requests.get(static_url)
        dynamic_response = requests.get(dynamic_url)
        
        if static_response.status_code != 200 or dynamic_response.status_code != 200:
            return None, None
        
        return static_response.json(), dynamic_response.json()
    
    """
    small_order_surcharge is the difference between order_minimum_no_surcharge 
    (as received from the Home Assignment API) and the cart value. 
    For example, if the cart value is 800 and order_minimum_no_surcharge is 1000, then the small_order_surcharge is 200. 
    small_order_surcharge can't be negative.
    """
    def get_small_order_surcharge (self,order_minimum_no_surcharge, cart_value):
        return (order_minimum_no_surcharge - cart_value) if cart_value < order_minimum_no_surcharge else 0
        
    # Straight-line formula
    def _straight_line(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        delta_lat = lat2 - lat1
        delta_lon = (lon2 - lon1) * cos((lat1 + lat2) / 2)  # Scale longitude by latitude
        return sqrt(delta_lat**2 + delta_lon**2) * 6371000

    # Haversine formula, apparently 1 degree latitude is about 111 km
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a = sin(delta_lat / 2)**2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    """
    Delivery distance is the straight line distance between the user's and venue's locations.
    Note that it's straight line distance, you don't need to figure out what's the distance via public roads. 
    The exact algorithm doesn't matter as long as it's a decent approximation of a straight line distance.
    """
    def get_delivery_distance(self,user_coords, venue_coords):
        user_lat, user_lon = user_coords
        venue_lat, venue_lon = venue_coords
        return self._straight_line(user_lat, user_lon, venue_lat, venue_lon)

    """
    Delivery fee can be calculated with: 
    base_price + a + b * distance / 10. 
    """
    def get_delivery_fee(self,distance, delivery_pricing):
        base_price = delivery_pricing['base_price']
        for range_info in delivery_pricing['distance_ranges']:
            min_dist = range_info['min']
            max_dist = range_info['max']
            if min_dist <= distance < max_dist or max_dist == 0:
                a = range_info['a']
                b = range_info['b']
                distance_component = round(b * distance / 10)
                return base_price + a + distance_component
        return None  # Delivery not available for this distance

    """
    Total price is the sum of cart value, small order surcharge, and delivery fee.
    """
    def get_total_price(self, cart_value, delivery_fee, small_order_surcharge):
        return cart_value + delivery_fee + small_order_surcharge

    """
    The DOPC service provide a single endpoint: GET /api/v1/delivery-order-price, which takes the following as query parameters (all are required):
    venue_slug (string): The unique identifier (slug) for the venue from which the delivery order will be placed
    cart_value: (integer): The total value of the items in the shopping cart
    user_lat (number with decimal point): The latitude of the user's location
    user_lon (number with decimal point): The longitude of the user's location
    """
    def get_delivery_order_price(self,venue_slug:str, cart_value:int, user_lat:float, user_lon:float):
        
        # Fetch venue data
        static_data, dynamic_data = self.fetch_venue_data(venue_slug)
        if not static_data or not dynamic_data:
            return {"error": "Venue data not found"}, 404

        venue_coords = tuple(static_data['venue_raw']['location']['coordinates'][::-1])  # [lon, lat] to (lat, lon)
        user_coords = (user_lat, user_lon)
        delivery_specs = dynamic_data['venue_raw']['delivery_specs']
        order_minimum_no_surcharge = delivery_specs['order_minimum_no_surcharge']
        delivery_pricing = delivery_specs['delivery_pricing']

        delivery_distance = self.get_delivery_distance(user_coords, venue_coords)
        delivery_fee = self.get_delivery_fee(delivery_distance, delivery_pricing)
        #check the delivery availablity 
        if delivery_fee is None:
            return {"error": "Delivery not available for this distance"}, 400
    
        small_order_surcharge = self.get_small_order_surcharge(order_minimum_no_surcharge, cart_value)
        # Calculate total price
        total_price = self.get_total_price(cart_value, delivery_fee, small_order_surcharge)
        
        # Construct response
        response = {
            "total_price": total_price,
            "small_order_surcharge": small_order_surcharge,
            "cart_value": cart_value,
            "delivery": {
                "fee": delivery_fee,
                "distance": round(delivery_distance)
            }
        }
        
        return response, 200
    

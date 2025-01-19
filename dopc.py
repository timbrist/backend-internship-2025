from flask import Flask, request, jsonify
import requests
from geopy.distance import geodesic

#Test json module 
import json


app = Flask(__name__)


class DOPC:
    def __init__(self, app, home_assignment_api = "https://consumer-api.development.dev.woltapi.com/home-assignment-api/v1/venues"):
        self.home_assignment_api = home_assignment_api
        self.app = app
        self.register_routes()


    def register_routes(self):
        self.app.add_url_rule(
            '/api/v1/delivery-order-price', 
            view_func=self.get_delivery_order_price, 
            methods=['GET']
        )

    def fetch_venue_data(self, venue_slug):
        """Fetch static and dynamic data for a given venue."""
        print("this is home api", self.home_assignment_api)
        static_url = f"{self.home_assignment_api}/{venue_slug}/static"
        dynamic_url = f"{self.home_assignment_api}/{venue_slug}/dynamic"
        print("this is url" ,static_url)
        static_response = requests.get(static_url)
        dynamic_response = requests.get(dynamic_url)
        
        if static_response.status_code != 200 or dynamic_response.status_code != 200:
            return None, None
        
        return static_response.json(), dynamic_response.json()
    
    def calculate_delivery_distance(self,user_coords, venue_coords):
        """Calculate the straight-line distance between user and venue."""
        return geodesic(user_coords, venue_coords).meters

    def calculate_delivery_fee(self,distance, delivery_pricing):
        """Calculate the delivery fee based on distance and pricing rules."""
        print("this is distance", distance)
        print("this is delivery_pricing", delivery_pricing)

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

    def get_delivery_order_price(self):
        # Extract query parameters
        venue_slug = request.args.get('venue_slug')
        cart_value = int(request.args.get('cart_value'))
        user_lat = float(request.args.get('user_lat'))
        user_lon = float(request.args.get('user_lon'))
        
        # Fetch venue data
        static_data, dynamic_data = self.fetch_venue_data(venue_slug)
        if not static_data or not dynamic_data:
            return jsonify({"error": "Venue data not found"}), 404
        
        # print("this is static_data", static_data)
        with open("data.json", "w") as json_file:
            json.dump(dynamic_data, json_file)
        print("json_list written to JSON file as a list.")

        # Extract venue coordinates
        venue_coords = tuple(static_data['venue_raw']['location']['coordinates'][::-1])  # [lon, lat] to (lat, lon)
        user_coords = (user_lat, user_lon)
        
        # Calculate delivery distance
        delivery_distance = self.calculate_delivery_distance(user_coords, venue_coords)
        
        # Calculate delivery fee
        delivery_pricing = dynamic_data['venue_raw']['delivery_specs']['delivery_pricing']
        delivery_fee = self.calculate_delivery_fee(delivery_distance, delivery_pricing)
        if delivery_fee is None:
            return jsonify({"error": "Delivery not available for this distance"}), 400
        
        # Calculate small order surcharge
        order_minimum_no_surcharge = dynamic_data['venue_raw']['delivery_specs']['order_minimum_no_surcharge']
        small_order_surcharge = (order_minimum_no_surcharge - cart_value) if cart_value < order_minimum_no_surcharge else 0
        
        # Calculate total price
        total_price = cart_value + delivery_fee + small_order_surcharge
        
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
        
        return jsonify(response)
    

DOPC(app)

if __name__ == '__main__':
    app.run(debug=True)

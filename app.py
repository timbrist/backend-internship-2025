from flask import Flask, request, jsonify
from dopc import DOPC

app = Flask(__name__)
delivery_order_price_calculator_service = DOPC()

@app.route('/api/v1/delivery-order-price', methods=['GET'])
def delivery_order_price():
    try:
        venue_slug = request.args.get('venue_slug')
        cart_value = int(request.args.get('cart_value'))
        user_lat = float(request.args.get('user_lat'))
        user_lon = float(request.args.get('user_lon'))

        response, status = delivery_order_price_calculator_service.get_delivery_order_price(
            venue_slug, cart_value, user_lat, user_lon
        )
        return jsonify(response), status

    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input parameters"}), 400

if __name__ == '__main__':
    app.run(debug=True)

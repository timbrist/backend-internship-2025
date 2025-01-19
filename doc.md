# Documentation of the Delivery Order Price Calculator service

Delivery Order Price Calculator service is developed in Python Language 3.9. 
it used a lightweight WSGI web framework : flask

### installation

If you want to have a clean python environment, use the following command lines:
```bash 
conda create -n dopc python=3.9
conda activate dopc
pip install -r requirements.txt
```

or else you would like to install the package into your local environment, only do :
```bash 
pip install -r requirements.txt
```

### Running Instructions

#### step 1: run the server
```bash
python app.py
```

#### step 2: test the server

You could either use curl to send a request as follow:
```bash
curl "http://localhost:8000/api/v1/delivery-order-price?venue_slug=home-assignment-venue-helsinki&cart_value=1000&user_lat=60.17094&user_lon=24.93087"
```
or just paste the http onto your browser and you will see:
```bash
{
  "cart_value": 1000,
  "delivery": {
    "distance": 177,
    "fee": 190
  },
  "small_order_surcharge": 0,
  "total_price": 1190
}
```

or you run the test script in the same directory as test_dopc.py 
```bash
python test_dopc.py
```



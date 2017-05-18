from flask import Flask
from flask import request
from flask import jsonify
import redis
import requests
import json
import os


REDIS_URL = os.environ.get('REDIS_URL')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)
r_server = redis.Redis.from_url(REDIS_URL)

@app.route('/')
def index():
  return "OK"

@app.route('/cache')
def cache():
  # try:
  address = request.args.get('address')
  if not address:
    jsonify({'status': 'err'})

  street = r_server.hget(address, 'street')
  house = r_server.hget(address, 'house')
  latitude = r_server.hget(address, 'latitude')
  longitude = r_server.hget(address, 'longitude')

  if street:
    street = street.decode('utf-8')
  if house:
    house = house.decode('utf-8')
  if latitude:
    latitude = latitude.decode('utf-8')
  if longitude:
    longitude = longitude.decode('utf-8')


  if not latitude and not longitude:
    service_response = requests.get("https://geocode-maps.yandex.ru/1.x/?geocode={}&format=json".format(address))
    if service_response.status_code != 200:
      jsonify({'status': 'err'})

    root = json.loads(service_response.text)

    found = int(root['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found'])
    print(found)
    feature_member = root['response']['GeoObjectCollection']['featureMember'][0]

    address_details = feature_member['GeoObject']['metaDataProperty']['GeocoderMetaData']
    print(address_details['kind'])
    print(address_details['text'])
    print(address_details['precision'])

    street = ''
    house = ''

    for address_component in address_details['Address']['Components']:
      if address_component['kind'] == 'locality' and address_component['name'] != 'Саратов':
        pass
      elif address_component['kind'] == 'street':
        street = address_component['name']
      elif address_component['kind'] == 'house':
        house = address_component['name']

    latitude = feature_member['GeoObject']['Point']['pos'].split()[0]
    longitude = feature_member['GeoObject']['Point']['pos'].split()[1]

    r_server.hset(address, 'street', street)
    r_server.hset(address, 'house', house)
    r_server.hset(address, 'latitude', latitude)
    r_server.hset(address, 'longitude', longitude)

  response = {
    'status': 'ok',
    'street': street,
    'house': house,
    'latitude': float(latitude),
    'longitude': float(longitude)
  }

  return jsonify(response)

  # except Exception as e:
  #   print(e)

  return jsonify({'status': 'err'})

if __name__ == "__main__":
  app.run(debug=False, host='0.0.0.0', port=PORT)

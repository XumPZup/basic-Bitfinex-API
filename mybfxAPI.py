import requests
import hashlib
import json
import time
import hmac


class Client:
    def __init__(self, API_KEY, API_SECRET, host='https://api.bitfinex.com/v2'):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.host = host
        self.session = requests.session()
        self.last_order = None
        self.wallets = None

    # [source] -> https://github.com/bitfinexcom/bitfinex-api-py/blob/master/bfxapi/utils/auth.py
    def _generate_auth_headers(self, path, body):
        nonce = str(self._gen_nonce())
        signature = "/api/v2/{}{}{}".format(path, nonce, body)
        h = hmac.new(self.API_SECRET.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
        signature = h.hexdigest()
        return {
            "bfx-nonce": nonce,
            "bfx-apikey": self.API_KEY,
            "bfx-signature": signature
            }

    def _gen_nonce(self):
        return int(round(time.time() * 1000000))

    def _gen_unique_cid(self):
        return int(round(time.time() * 1000))

    # - [source] -> https://github.com/akcarsten/bitfinex_api/blob/master/bitfinex/bitfinex_v2.py
    def post(self, endpoint, data={}, params=''):
        url = f'{self.host}/{endpoint}'
        sData = json.dumps(data)
        headers = self._generate_auth_headers(endpoint, sData)
        headers["content-type"] = "application/json"
        self.session.headers = headers
        with self.session.request('POST', url, data=sData) as response:
            text = response.text
            if response.ok:
                print('SUCCESS')
                return json.loads(text, parse_float=float)
            else:
                print('[!] REQUEST FAILED')


    def get_wallets(self):
        endpoint = 'auth/r/wallets'
        raw_wallets = self.post(endpoint)
        self.wallets = [(wallet[1], wallet[2]) for wallet in raw_wallets]
        return self.wallets


    def get_active_orders(self, symbol):
        endpoint = "auth/r/orders/{}".format(symbol)
        raw_orders = self.post(endpoint)
        return raw_orders


    def submit_limit_order(self, symbol, price, amount):
        endpoint = "auth/w/order/submit"
        cid = self._gen_unique_cid()
        payload = {
            "cid": cid,
            "type": 'EXCHANGE LIMIT',
            "symbol": symbol,
            "amount": str(amount),
            "price": str(price),
            "meta": {},
            "flags": 0
        }
        raw_notification = self.post(endpoint, payload)
        self.last_order = raw_notification[4][0]
        return raw_notification[4][0]
    

    def cancel_last_order(self):
        endpoint = "auth/w/order/cancel"
        if self.last_order == None:
            return
        raw_notification = self.post(endpoint, { 'id': self.last_order[0] })
        self.last_order = None
        return raw_notification[4][0]


if __name__ == '__main__':
    c = None
    with open('credAPI.txt', 'r') as f:
        k, s = f.read().split()
        c = Client(k, s)

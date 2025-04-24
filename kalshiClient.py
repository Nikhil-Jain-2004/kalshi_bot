import requests
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import utils
import datetime


class KalshiClient:
    def __init__(
        self,
        key_id,
        private_key_path,
        base_url="https://api.elections.kalshi.com/trade-api/v2",
    ):
        self.key_id = key_id
        self.base_url = base_url
        self.session = requests.Session()

        with open(private_key_path, "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )

    def _generate_headers(self, method, path):
        timestamp = utils.get_curr_time_milliseconds()
        timestamp_str = str(timestamp)
        payload = f"{timestamp_str}.{method.upper()}.{path}".encode("utf-8")
        try:
            signature = self.private_key.sign(
                payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH,
                ),
                hashes.SHA256(),
            )
            signature = base64.b64encode(signature).decode("utf-8")
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }

    def _request(self, method, endpoint, params=None, data=None):
        path = endpoint if endpoint.startswith("/") else "/" + endpoint
        url = f"{self.base_url}{path}"
        headers = self._generate_headers(method, path)
        response = self.session.request(
            method=method.upper(),
            url=url, headers=headers,
            params=params,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint, params=None):
        return self._request("GET", endpoint, params=params)

    def _post(self, endpoint, data=None):
        return self._request("POST", endpoint, data=data)

    def _put(self, endpoint, data=None):
        return self._request("PUT", endpoint, data=data)

    def _delete(self, endpoint):
        return self._request("DELETE", endpoint)

    # Public
    def get_api_version(self):
        return self._get("/api_version")

    # Communications
    def get_communications_id(self):
        return self._get("/communications/id")

    def get_quotes(self):
        return self._get("/communications/quotes")

    def create_quote(self, data):
        return self._post("/communications/quotes", data)

    def get_quote(self, quote_id):
        return self._get(f"/communications/quotes/{quote_id}")

    def delete_quote(self, quote_id):
        return self._delete(f"/communications/quotes/{quote_id}")

    def accept_quote(self, quote_id):
        return self._put(f"/communications/quotes/{quote_id}/accept")

    def confirm_quote(self, quote_id):
        return self._put(f"/communications/quotes/{quote_id}/confirm")

    def get_rfqs(self):
        return self._get("/communications/rfqs")

    def create_rfq(self, data):
        return self._post("/communications/rfqs", data)

    def get_rfq(self, rfq_id):
        return self._get(f"/communications/rfqs/{rfq_id}")

    def delete_rfq(self, rfq_id):
        return self._delete(f"/communications/rfqs/{rfq_id}")

    # Market
    def get_events(self):
        return self._get("/events")

    def get_event(self, event_ticker):
        return self._get(f"/events/{event_ticker}")

    def get_markets(self):
        return self._get("/markets?limit=1000")

    def get_market(self, market_ticker):
        return self._get(f"/markets/{market_ticker}")

    def get_market_orderbook(self, market_ticker):
        return self._get(f"/markets/{market_ticker}/orderbook")

    def get_trades(self):
        return self._get(f"/markets/trades")

    def get_series_list(self):
        return self._get("/series/")

    def get_series(self, series_ticker):
        return self._get(f"/series/{series_ticker}")

    def get_market_candlesticks(
        self,
        series_ticker,
        market_ticker,
        start_ts: datetime.datetime,
        end_ts: datetime.datetime,
        period_interval: str
    ):
        params = {
            "start_ts": utils.get_seconds_since_epoch(start_ts),
            "end_ts": utils.get_seconds_since_epoch(end_ts),
            "period_interval": utils.get_period_interval(period_interval)
        }
        return self._get(
            f"/series/{series_ticker}/markets/{market_ticker}/candlesticks",
            params=params
        )

    # Exchange
    def get_announcements(self):
        return self._get("/exchange/announcements")

    def get_schedule(self):
        return self._get("/exchange/schedule")

    def get_status(self):
        return self._get("/exchange/status")

    def get_user_data_timestamp(self):
        return self._get("/exchange/user_data_timestamp")

    # Portfolio
    def get_balance(self):
        return self._get("/portfolio/balance")

    def get_fills(self):
        return self._get("/portfolio/fills")

    def get_orders(self):
        return self._get("/portfolio/orders")

    def create_order(self, data):
        return self._post("/portfolio/orders", data)

    def batch_create_orders(self, data):
        return self._post("/portfolio/orders/batched", data)

    def batch_cancel_orders(self, data):
        return self._delete("/portfolio/orders/batched", data)

    def get_order(self, order_id):
        return self._get(f"/portfolio/orders/{order_id}")

    def cancel_order(self, order_id):
        return self._delete(f"/portfolio/orders/{order_id}")

    def amend_order(self, order_id, data):
        return self._post(f"/portfolio/orders/{order_id}/amend", data)

    def decrease_order(self, order_id, data):
        return self._post(f"/portfolio/orders/{order_id}/decrease", data)

    def get_positions(self):
        return self._get("/portfolio/positions")

    def get_settlements(self):
        return self._get("/portfolio/settlements")

    def get_resting_order_total_value(self):
        return self._get("/portfolio/summary/resting_order_total_value")

    # Milestone
    def get_milestones(self):
        return self._get("/milestones/")

    def get_milestone(self, milestone_id):
        return self._get(f"/milestones/{milestone_id}")

    # Collections
    def get_collections(self):
        return self._get("/multivariate_event_collections/")

    def get_collection(self, collection_id):
        return self._get(f"/multivariate_event_collections/{collection_id}")

    def create_market_in_collection(self, collection_id):
        return self._post(f"/multivariate_event_collections/{collection_id}")

    def get_collection_lookup_history(self, collection_id):
        return self._get(f"/multivariate_event_collections/{collection_id}/lookup")

    def lookup_tickers_in_collection(self, collection_id):
        return self._put(f"/multivariate_event_collections/{collection_id}/lookup")

    # Structured Target
    def get_structured_target(self, target_id):
        return self._get(f"/structured_targets/{target_id}")

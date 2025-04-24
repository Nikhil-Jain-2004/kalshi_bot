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

    def get_quotes(
        self,
        cursor=None,
        limit=None,
        market_ticker=None,
        event_ticker=None,
        status=None,
        quote_creator_user_id=None,
        rfq_creator_user_id=None,
        rfq_id=None
    ):
        params = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if market_ticker is not None:
            params["market_ticker"] = market_ticker
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
        if status is not None:
            params["status"] = status
        if quote_creator_user_id is not None:
            params["quote_creator_user_id"] = quote_creator_user_id
        if rfq_creator_user_id is not None:
            params["rfq_creator_user_id"] = rfq_creator_user_id
        if rfq_id is not None:
            params["rfq_id"] = rfq_id

        return self._get("/communications/quotes", params=params)

    def create_quote(
        self,
        rfq_id=None,
        yes_bid=None,
        no_bid=None,
        rest_remainder=None
    ):
        params = {}
        if rfq_id is not None:
            params["rfq_id"] = rfq_id
        if yes_bid is not None:
            params["yes_bid"] = yes_bid
        if no_bid is not None:
            params["no_bid"] = no_bid
        if rest_remainder is not None:
            params["rest_remainder"] = rest_remainder

        return self._post("/communications/quotes", params=params)

    def get_quote(self, quote_id):
        return self._get(f"/communications/quotes/{quote_id}")

    def delete_quote(self, quote_id):
        return self._delete(f"/communications/quotes/{quote_id}")

    def accept_quote(self, quote_id, data):
        return self._put(f"/communications/quotes/{quote_id}/accept", data)

    def confirm_quote(self, quote_id):
        return self._put(f"/communications/quotes/{quote_id}/confirm")

    def get_rfqs(
        self,
        cursor=None,
        limit=None,
        market_ticker=None,
        event_ticker=None,
        status=None,
        creator_user_id=None
    ):
        params = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if market_ticker is not None:
            params["market_ticker"] = market_ticker
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
        if status is not None:
            params["status"] = status
        if creator_user_id is not None:
            params["creator_user_id"] = creator_user_id
        
        return self._get("/communications/rfqs", params=params)

    def create_rfq(
        self,
        market_ticker=None,
        contracts=None,
        rest_remainder=None
    ):
        params = {}
        if market_ticker is not None:
            params["market_ticker"] = market_ticker
        if contracts is not None:
            params["contracts"] = contracts
        if rest_remainder is not None:
            params["rest_remainder"] = rest_remainder
    
        return self._post("/communications/rfqs", params=params)

    def get_rfq(self, rfq_id):
        return self._get(f"/communications/rfqs/{rfq_id}")

    def delete_rfq(self, rfq_id):
        return self._delete(f"/communications/rfqs/{rfq_id}")

    # Market
    def get_events(
        self,
        limit=None,
        cursor=None,
        status=None,
        series_ticker=None,
        with_nested_markets=None
    ):
        params = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if status is not None:
            params["status"] = status
        if series_ticker is not None:
            params["series_ticker"] = series_ticker
        if with_nested_markets is not None:
            params["with_nested_markets"] = with_nested_markets
        
        return self._get("/events", params=params)

    def get_event(self, event_ticker, with_nested_markets=None):
        params = {}
        if with_nested_markets is not None:
            params["with_nested_markets"] = with_nested_markets

        return self._get(f"/events/{event_ticker}", params=params)

    def get_markets(
        self,
        limit=None,
        cursor=None,
        event_ticker=None,
        series_ticker=None,
        max_close_ts=None,
        min_close_ts=None,
        status=None,
        tickers=None
    ):
        params = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
        if series_ticker is not None:
            params["series_ticker"] = series_ticker
        if max_close_ts is not None:
            params["max_close_ts"] = max_close_ts
        if min_close_ts is not None:
            params["min_close_ts"] = min_close_ts
        if status is not None:
            params["status"] = status
        if tickers is not None:
            params["tickers"] = tickers

        return self._get("/markets?limit=1000", params=params)

    def get_trades(
        self,
        cursor=None,
        limit=None,
        ticker=None,
        min_ts=None,
        max_ts=None
    ):
        params = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if ticker is not None:
            params["ticker"] = ticker
        if min_ts is not None:
            params["min_ts"] = min_ts
        if max_ts is not None:
            params["max_ts"] = max_ts

        return self._get("/markets/trades", params=params)

    def get_market(self, market_ticker):
        return self._get(f"/markets/{market_ticker}")

    def get_market_orderbook(self, market_ticker, depth=None):
        params = {}
        if depth is not None:
            params["depth"] = depth

        return self._get(f"/markets/{market_ticker}/orderbook", params=params)

    def get_series_list(self, category=None, include_product_metadata=None):
        params = {}
        if category is not None:
            params["category"] = category
        if include_product_metadata is not None:
            params["include_product_metadata"] = include_product_metadata

        return self._get("/series/", params=params)

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

    # Milestone
    def get_milestones(
        self,
        limit,
        minimum_start_date=None,
        category=None,
        _type=None,
        related_event_ticker=None,
        cursor=None
    ):
        params = {
            "limit": limit
        }
        if minimum_start_date is not None:
            params["minimum_start_date"] = minimum_start_date
        if category is not None:
            params["category"] = category
        if _type is not None:
            params["type"] = _type
        if related_event_ticker is not None:
            params["related_event_ticker"] = related_event_ticker
        if cursor is not None:
            params["cursor"] = cursor

        return self._get("/milestones/", params=params)

    def get_milestone(self, milestone_id):
        return self._get(f"/milestones/{milestone_id}")

    '''
    # Commenting out until we need to use

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
    '''

    # Portfolio
    def get_balance(self):
        return self._get("/portfolio/balance")

    def get_fills(
        self,
        ticker=None,
        min_ts=None,
        max_ts=None,
        limit=None,
        cursor=None,
    ):
        params = {}
        if ticker is not None:
            params["ticker"] = ticker
        if min_ts is not None:
            params["min_ts"] = min_ts
        if max_ts is not None:
            params["max_ts"] = max_ts
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return self._get("/portfolio/fills", params=params)

    def get_orders(
        self,
        ticker=None,
        event_ticker=None,
        min_ts=None,
        max_ts=None,
        status=None,
        cursor=None,
        limit=None,
    ):
        params = {}
        if ticker is not None:
            params["ticker"] = ticker
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
        if min_ts is not None:
            params["min_ts"] = min_ts
        if max_ts is not None:
            params["max_ts"] = max_ts
        if status is not None:
            params["status"] = status
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit

        return self._get("/portfolio/orders", params=params)

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

    def get_positions(
        self,
        cursor=None,
        limit=None,
        count_filter=None,
        settlement_status=None,
        ticker=None,
        event_ticker=None,
    ):
        params = {}
        if cursor is not None:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if count_filter is not None:
            params["count_filter"] = count_filter
        if settlement_status is not None:
            params["settlement_status"] = settlement_status
        if ticker is not None:
            params["ticker"] = ticker
        if event_ticker is not None:
            params["event_ticker"] = event_ticker
    
        return self._get("/portfolio/positions", params=params)

    def get_portfolio_settlements(
        self,
        limit=None,
        min_ts=None,
        max_ts=None,
        cursor=None
    ):
        params = {}
        if limit is not None:
            params["limit"] = limit
        if min_ts is not None:
            params["min_ts"] = min_ts
        if max_ts is not None:
            params["max_ts"] = max_ts
        if cursor is not None:
            params["cursor"] = cursor

        return self._get("/portfolio/settlements", params=params)

    def get_portfolio_resting_order_total_value(self):
        return self._get("/portfolio/summary/resting_order_total_value")

    # Structured Target
    def get_structured_target(self, structured_target_id):
        return self._get(f"/structured_targets/{structured_target_id}")

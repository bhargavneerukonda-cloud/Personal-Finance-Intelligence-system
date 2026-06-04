"""
Plaid API service for bank account connection and transaction sync.

Plaid Link flow:
  1. Frontend calls POST /accounts/plaid/link-token to get a link_token
  2. Frontend opens Plaid Link widget with link_token
  3. User authenticates with their bank
  4. Frontend receives public_token from Plaid Link
  5. Frontend calls POST /accounts/plaid/exchange with public_token
  6. Backend exchanges public_token for access_token (stored securely)
  7. Backend fetches accounts and transactions using access_token
"""
import os
from typing import Optional
from datetime import datetime, timedelta


class PlaidService:
    """Wrapper around Plaid Python SDK for financial data aggregation."""

    def __init__(self):
        self.client_id = os.environ.get("PLAID_CLIENT_ID", "")
        self.secret = os.environ.get("PLAID_SECRET", "")
        self.env = os.environ.get("PLAID_ENV", "sandbox")
        self._client = None

    def _get_client(self):
        """Lazily initialize Plaid client."""
        if self._client is None:
            try:
                import plaid
                from plaid.api import plaid_api
                from plaid.model.products import Products
                from plaid.model.country_code import CountryCode

                env_map = {
                    "sandbox": plaid.Environment.Sandbox,
                    "development": plaid.Environment.Development,
                    "production": plaid.Environment.Production,
                }
                configuration = plaid.Configuration(
                    host=env_map.get(self.env, plaid.Environment.Sandbox),
                    api_key={"clientId": self.client_id, "secret": self.secret},
                )
                api_client = plaid.ApiClient(configuration)
                self._client = plaid_api.PlaidApi(api_client)
            except ImportError:
                raise RuntimeError("plaid-python not installed. Add to requirements.txt")
        return self._client

    def create_link_token(self, user_id: str) -> dict:
        """
        Create a Plaid Link token for frontend Link widget initialization.
        Returns: {"link_token": "link-sandbox-...", "expiration": "..."}
        """
        try:
            from plaid.model.link_token_create_request import LinkTokenCreateRequest
            from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
            from plaid.model.products import Products
            from plaid.model.country_code import CountryCode

            request = LinkTokenCreateRequest(
                products=[Products("transactions")],
                client_name="FinSight AI",
                country_codes=[CountryCode("US")],
                language="en",
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
            )
            response = self._get_client().link_token_create(request)
            return {"link_token": response["link_token"], "expiration": str(response["expiration"])}
        except Exception as e:
            raise RuntimeError(f"Failed to create link token: {e}")

    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange public_token (from Plaid Link) for permanent access_token.
        Returns: access_token (store securely in Secrets Manager)
        """
        try:
            from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self._get_client().item_public_token_exchange(request)
            return response["access_token"]
        except Exception as e:
            raise RuntimeError(f"Token exchange failed: {e}")

    def get_accounts(self, access_token: str) -> list:
        """Fetch all accounts for a Plaid item."""
        try:
            from plaid.model.accounts_get_request import AccountsGetRequest
            request = AccountsGetRequest(access_token=access_token)
            response = self._get_client().accounts_get(request)
            accounts = []
            for acct in response["accounts"]:
                accounts.append({
                    "plaid_account_id": acct["account_id"],
                    "account_name": acct["name"],
                    "account_type": str(acct["type"]),
                    "balance": float(acct["balances"]["current"] or 0),
                    "currency": acct["balances"].get("iso_currency_code", "USD"),
                })
            return accounts
        except Exception as e:
            raise RuntimeError(f"Failed to fetch accounts: {e}")

    def get_transactions(self, access_token: str, days_back: int = 30) -> list:
        """
        Fetch recent transactions from Plaid.
        Uses the newer /transactions/sync endpoint for incremental updates.
        Falls back to /transactions/get for initial load.
        """
        try:
            from plaid.model.transactions_get_request import TransactionsGetRequest
            from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
            import datetime as dt

            end_date = dt.date.today()
            start_date = end_date - timedelta(days=days_back)

            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=TransactionsGetRequestOptions(count=500),
            )
            response = self._get_client().transactions_get(request)
            transactions = []
            for tx in response["transactions"]:
                transactions.append({
                    "plaid_transaction_id": tx["transaction_id"],
                    "plaid_account_id": tx["account_id"],
                    "amount": float(tx["amount"]),
                    "merchant_name": tx.get("merchant_name") or tx.get("name", ""),
                    "description": tx.get("name", ""),
                    "transaction_date": str(tx["date"]),
                    "category_plaid": tx.get("category", []),
                    "pending": tx.get("pending", False),
                })
            return transactions
        except Exception as e:
            raise RuntimeError(f"Failed to fetch transactions: {e}")


# Singleton
plaid_service = PlaidService()

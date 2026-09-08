
import os
import requests


class CourtListenerClient:
    """
    Prototype client for retrieving case law from CourtListener.

    The client supports keyword-based case-law searches and returns
    normalized evidence records suitable for the LegalMind Research Agent.
    """

    BASE_URL = "https://www.courtlistener.com/api/rest/v4"

    def __init__(self, api_token=None):
        self.api_token = api_token or os.getenv("COURTLISTENER_API_TOKEN")

        self.session = requests.Session()

        if self.api_token:
            self.session.headers.update({
                "Authorization": f"Token {self.api_token}"
            })

        self.session.headers.update({
            "User-Agent": "LegalMind-Research-Agent/1.0"
        })

    def search_opinions(
        self,
        query,
        limit=5,
        court=None
    ):
        """
        Search CourtListener opinions.

        Parameters
        ----------
        query : str
            Legal research query.

        limit : int
            Maximum number of results.

        court : str or None
            Optional CourtListener court identifier.

        Returns
        -------
        list
            Normalized case-law evidence records.
        """

        url = f"{self.BASE_URL}/search/"

        params = {
            "q": query,
            "type": "o",
            "order_by": "dateFiled desc",
            "page_size": min(limit, 20)
        }

        if court:
            params["court"] = court

        response = self.session.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("results", [])[:limit]:

            results.append({
                "source": "CourtListener",
                "corpus": "case_law",
                "jurisdiction": (
                    item.get("court_citation_string")
                    or item.get("court")
                ),
                "case_name": (
                    item.get("caseName")
                    or item.get("case_name")
                ),
                "date_filed": item.get("dateFiled"),
                "citation": item.get("citation"),
                "docket_number": item.get("docketNumber"),
                "absolute_url": item.get("absolute_url"),
                "snippet": item.get("snippet"),
                "text": (
                    item.get("plain_text")
                    or item.get("html_with_citations")
                    or item.get("snippet")
                ),
                "source_id": (
                    item.get("cluster_id")
                    or item.get("id")
                )
            })

        return results

    def search_opinions_with_content(
        self,
        query,
        limit=5,
        court=None
    ):
        """
        Search CourtListener opinions and retrieve full opinion text.

        This follows the search result's first opinion ID to the
        dedicated /opinions/{opinion_id}/ endpoint so that actual
        opinion content is available to the Research Agent.
        """

        url = f"{self.BASE_URL}/search/"

        params = {
            "q": query,
            "type": "o",
            "order_by": "dateFiled desc",
            "page_size": min(limit, 20)
        }

        if court:
            params["court"] = court

        response = self.session.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("results", [])[:limit]:

            opinions = item.get("opinions") or []

            if not opinions:
                continue

            actual_opinion_id = opinions[0].get("id")

            if not actual_opinion_id:
                continue

            opinion_url = (
                f"{self.BASE_URL}/opinions/{actual_opinion_id}/"
            )

            opinion_response = self.session.get(
                opinion_url,
                timeout=30
            )

            opinion_response.raise_for_status()

            opinion_data = opinion_response.json()

            text = (
                opinion_data.get("plain_text")
                or opinion_data.get("html_with_citations")
                or opinion_data.get("html")
            )

            results.append({
                "source": "CourtListener",
                "corpus": "case_law",
                "jurisdiction": (
                    item.get("court_citation_string")
                    or item.get("court")
                ),
                "case_name": (
                    item.get("caseName")
                    or item.get("case_name")
                ),
                "date_filed": item.get("dateFiled"),
                "citation": item.get("citation"),
                "docket_number": item.get("docketNumber"),
                "absolute_url": item.get("absolute_url"),
                "snippet": item.get("snippet"),
                "text": text,
                "opinion_id": actual_opinion_id,
                "cluster_id": item.get("id"),
                "source_id": actual_opinion_id
            })

        return results

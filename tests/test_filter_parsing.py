import pytest
from unittest.mock import patch


class TestFilterParsing:
    """Test natural language filter parsing"""

    @patch("src.services.search_service.settings")
    def test_extracts_price_from_under(self, mock_settings):
        """GIVEN 'shoes under $100' WHEN parse THEN max_price=100"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("shoes under $100")

        assert result["max_price"] == 100.0

    @patch("src.services.search_service.settings")
    def test_extracts_price_from_less_than(self, mock_settings):
        """GIVEN 'less than $50' WHEN parse THEN max_price=50"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("headphones less than $50")

        assert result["max_price"] == 50.0

    @patch("src.services.search_service.settings")
    def test_extracts_price_from_budget(self, mock_settings):
        """GIVEN 'budget of $200' WHEN parse THEN max_price=200"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("shirt budget of $200")

        assert result["max_price"] == 200.0

    @patch("src.services.search_service.settings")
    def test_extracts_gender_mens(self, mock_settings):
        """GIVEN 'men's shoes' WHEN parse THEN gender='men'"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("men's shoes")

        assert result["gender"] == "men"

    @patch("src.services.search_service.settings")
    def test_extracts_gender_for_him(self, mock_settings):
        """GIVEN 'for him' WHEN parse THEN gender='men'"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("gift for him")

        assert result["gender"] == "men"

    @patch("src.services.search_service.settings")
    def test_extracts_gender_womens(self, mock_settings):
        """GIVEN 'women's dress' WHEN parse THEN gender='women'"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("women's dress")

        assert result["gender"] == "women"

    @patch("src.services.search_service.settings")
    def test_extracts_category_headphones(self, mock_settings):
        """GIVEN 'wireless headphones' WHEN parse THEN category='Electronics'"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("wireless headphones")

        assert result["category"] == "Electronics"

    @patch("src.services.search_service.settings")
    def test_extracts_category_shoes(self, mock_settings):
        """GIVEN 'running shoes' WHEN parse THEN category='Fashion'"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("running shoes")

        assert result["category"] == "Fashion"

    @patch("src.services.search_service.settings")
    def test_extracts_category_moisturizer(self, mock_settings):
        """GIVEN 'face moisturizer' WHEN parse THEN category='Beauty'"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("face moisturizer")

        assert result["category"] == "Beauty"

    @patch("src.services.search_service.settings")
    def test_no_filters_returns_none(self, mock_settings):
        """GIVEN query with no filters WHEN parse THEN all filters are None"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("best products")

        assert result["max_price"] is None
        assert result["category"] is None
        assert result["gender"] is None

    @patch("src.services.search_service.settings")
    def test_combined_filters(self, mock_settings):
        """GIVEN 'men's shoes under $100' WHEN parse THEN extracts all filters"""
        mock_settings.cohere_api_key = "test"
        from src.services.search_service import SearchService

        service = SearchService()
        result = service.parse_natural_language("men's shoes under $100")

        assert result["max_price"] == 100.0
        assert result["gender"] == "men"
        assert result["category"] == "Fashion"

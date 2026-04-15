import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from scripts.ingest_products import generate_embeddings, create_embedding_text


class TestEmbeddingGenerator:
    """Test embedding generation functionality"""

    def test_combines_text_correctly(self):
        """GIVEN product WHEN create_embedding_text THEN text includes name, description, brand, category"""
        product = {
            "name": "Men Black Running Shoes",
            "description": "Lightweight running shoes with cushioned sole",
            "brand": "Nike",
            "category": "Fashion",
        }
        text = create_embedding_text(product)

        assert "Men Black Running Shoes" in text
        assert "Lightweight running shoes" in text
        assert "Nike" in text
        assert "Fashion" in text

    @pytest.mark.asyncio
    async def test_generates_1024_dimensional_embeddings(self):
        """GIVEN product WHEN embed THEN embedding length is 1024"""
        mock_response = MagicMock()
        # Cohere v6 API returns embeddings as a dict with 'float' key
        mock_response.embeddings = {"float": [[0.1] * 1024]}

        mock_cohere = AsyncMock()
        mock_cohere.embed = AsyncMock(return_value=mock_response)

        products = [
            {
                "name": "Test Product",
                "description": "Test description",
                "brand": "TestBrand",
                "category": "Fashion",
            }
        ]

        result = await generate_embeddings(products, mock_cohere)

        assert "embedding" in result[0]
        assert len(result[0]["embedding"]) == 1024

    @pytest.mark.asyncio
    async def test_retries_on_api_failure(self):
        """GIVEN Cohere API timeout WHEN embed THEN retries up to 3 times with exponential backoff"""
        mock_cohere = AsyncMock()
        mock_cohere.embed = AsyncMock(
            side_effect=[
                Exception("Timeout"),
                Exception("Timeout"),
                MagicMock(embeddings=[MagicMock(embedding=[0.1] * 1024)]),
            ]
        )

        products = [
            {
                "name": "Test Product",
                "description": "Test description",
                "brand": "TestBrand",
                "category": "Fashion",
            }
        ]

        result = await generate_embeddings(products, mock_cohere)

        assert mock_cohere.embed.call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_raises_error(self):
        """GIVEN Cohere API fails 3 times THEN raises error"""
        mock_cohere = AsyncMock()
        mock_cohere.embed = AsyncMock(side_effect=Exception("API Error"))

        products = [
            {
                "name": "Test Product",
                "description": "Test description",
                "brand": "TestBrand",
                "category": "Fashion",
            }
        ]

        with pytest.raises(Exception, match="API Error"):
            await generate_embeddings(products, mock_cohere)

        assert mock_cohere.embed.call_count == 3

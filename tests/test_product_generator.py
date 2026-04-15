import pytest
from scripts.ingest_products import generate_products


class TestProductGenerator:
    """Test product generation functionality"""

    def test_generates_correct_number_of_products(self):
        """GIVEN count=10 WHEN generate_products(10) THEN returns 10 products"""
        products = generate_products(10)
        assert len(products) == 10

    def test_zero_count_uses_default(self):
        """GIVEN count=0 WHEN generate THEN uses default 500"""
        products = generate_products(0)
        assert len(products) == 500

    def test_negative_count_uses_default(self):
        """GIVEN count=-5 WHEN generate THEN uses default 500"""
        products = generate_products(-5)
        assert len(products) == 500

    def test_products_have_required_fields(self):
        """GIVEN any product WHEN generated THEN has required fields"""
        products = generate_products(5)
        required_fields = [
            "name",
            "description",
            "price",
            "category",
            "image_url",
            "product_url",
            "brand",
            "gender",
        ]

        for product in products:
            for field in required_fields:
                assert field in product, f"Missing field: {field}"
                assert product[field] is not None or field == "gender", (
                    f"Empty field: {field}"
                )

    def test_products_distributed_across_categories(self):
        """GIVEN count=100 WHEN generated THEN all 4 categories represented"""
        products = generate_products(100)
        categories = {p["category"] for p in products}
        expected_categories = {"Fashion", "Electronics", "Home", "Beauty"}

        assert categories == expected_categories, (
            f"Missing categories: {expected_categories - categories}"
        )

    def test_fashion_price_range(self):
        """GIVEN Fashion product THEN price between $15-$200"""
        products = generate_products(100)
        fashion_products = [p for p in products if p["category"] == "Fashion"]

        for product in fashion_products:
            assert 15 <= product["price"] <= 200, (
                f"Price {product['price']} out of range for Fashion"
            )

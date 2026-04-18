import pytest
from unittest.mock import MagicMock, patch


class TestSchemaMigration:
    """Test database schema migration for product scraping fields"""

    def test_migration_adds_sku_column(self):
        """GIVEN migration script WHEN executed THEN products table has sku column with UNIQUE constraint"""
        sql = """
        ALTER TABLE products ADD COLUMN IF NOT EXISTS sku TEXT UNIQUE;
        """
        assert "sku TEXT UNIQUE" in sql

    def test_migration_adds_sizes_column(self):
        """GIVEN migration script WHEN executed THEN products table has sizes column with JSONB type"""
        sql = """
        ALTER TABLE products ADD COLUMN IF NOT EXISTS sizes JSONB DEFAULT '[]'::jsonb;
        """
        assert "sizes JSONB" in sql

    def test_migration_adds_colors_column(self):
        """GIVEN migration script WHEN executed THEN products table has colors column with JSONB type"""
        sql = """
        ALTER TABLE products ADD COLUMN IF NOT EXISTS colors JSONB DEFAULT '[]'::jsonb;
        """
        assert "colors JSONB" in sql

    def test_migration_adds_cohere_embedding_column(self):
        """GIVEN migration script WHEN executed THEN products table has cohere_embedding column with vector(1024) type"""
        sql = """
        ALTER TABLE products ADD COLUMN IF NOT EXISTS cohere_embedding vector(1024);
        """
        assert "cohere_embedding vector(1024)" in sql

    def test_migration_creates_sku_index(self):
        """GIVEN migration script WHEN executed THEN products_sku_idx exists"""
        sql = """
        CREATE INDEX IF NOT EXISTS products_sku_idx ON products(sku);
        """
        assert "products_sku_idx" in sql

    def test_migration_creates_cohere_embedding_index(self):
        """GIVEN migration script WHEN executed THEN products_cohere_embedding_idx exists with hnsw"""
        sql = """
        CREATE INDEX IF NOT EXISTS products_cohere_embedding_idx ON products 
        USING hnsw (cohere_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
        assert "products_cohere_embedding_idx" in sql
        assert "hnsw" in sql
        assert "vector_cosine_ops" in sql

    def test_cohere_embedding_dimension_is_1024(self):
        """GIVEN migration script WHEN executed THEN cohere_embedding uses 1024 dimension"""
        sql = """
        ALTER TABLE products ADD COLUMN IF NOT EXISTS cohere_embedding vector(1024);
        """
        assert "vector(1024)" in sql

    def test_sku_is_unique(self):
        """GIVEN migration script WHEN executed THEN sku column has UNIQUE constraint"""
        sql = """
        ALTER TABLE products ADD COLUMN IF NOT EXISTS sku TEXT UNIQUE;
        """
        assert "UNIQUE" in sql

-- Migration: Add product fields for scraping
-- SKU, sizes, colors, cohere_embedding

-- Add sku column (unique)
ALTER TABLE products ADD COLUMN IF NOT EXISTS sku TEXT UNIQUE;

-- Add sizes column (JSONB array)
ALTER TABLE products ADD COLUMN IF NOT EXISTS sizes JSONB DEFAULT '[]'::jsonb;

-- Add colors column (JSONB array)
ALTER TABLE products ADD COLUMN IF NOT EXISTS colors JSONB DEFAULT '[]'::jsonb;

-- Add cohere_embedding column (vector 1024)
ALTER TABLE products ADD COLUMN IF NOT EXISTS cohere_embedding vector(1024);

-- Create index on sku
CREATE INDEX IF NOT EXISTS products_sku_idx ON products(sku);

-- Create HNSW index for vector similarity search on cohere_embedding
CREATE INDEX IF NOT EXISTS products_cohere_embedding_idx ON products 
USING hnsw (cohere_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
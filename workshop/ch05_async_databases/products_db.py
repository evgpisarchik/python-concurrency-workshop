"""Listing 5.2: schema for the e-commerce `products` database, plus data helpers.

Tables: brand -> product -> sku <- product_size / product_color
"""

from pathlib import Path

CREATE_BRAND_TABLE = """
    CREATE TABLE IF NOT EXISTS brand(
        brand_id SERIAL PRIMARY KEY,
        brand_name TEXT NOT NULL
    );"""

CREATE_PRODUCT_TABLE = """
    CREATE TABLE IF NOT EXISTS product(
        product_id SERIAL PRIMARY KEY,
        product_name TEXT NOT NULL,
        brand_id INT NOT NULL,
        FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
    );"""

CREATE_PRODUCT_COLOR_TABLE = """
    CREATE TABLE IF NOT EXISTS product_color(
        product_color_id SERIAL PRIMARY KEY,
        product_color_name TEXT NOT NULL
    );"""

CREATE_PRODUCT_SIZE_TABLE = """
    CREATE TABLE IF NOT EXISTS product_size(
        product_size_id SERIAL PRIMARY KEY,
        product_size_name TEXT NOT NULL
    );"""

CREATE_SKU_TABLE = """
    CREATE TABLE IF NOT EXISTS sku(
       sku_id SERIAL PRIMARY KEY,
       product_id INT NOT NULL,
       product_size_id INT NOT NULL,
       product_color_id INT NOT NULL,
       FOREIGN KEY (product_id) REFERENCES product(product_id),
       FOREIGN KEY (product_size_id) REFERENCES product_size(product_size_id),
       FOREIGN KEY (product_color_id) REFERENCES product_color(product_color_id)
    );"""

COLOR_INSERT = """
    INSERT INTO product_color VALUES(1, 'Blue') ON CONFLICT DO NOTHING;
    INSERT INTO product_color VALUES(2, 'Black') ON CONFLICT DO NOTHING;
    """

SIZE_INSERT = """
    INSERT INTO product_size VALUES(1, 'Small') ON CONFLICT DO NOTHING;
    INSERT INTO product_size VALUES(2, 'Medium') ON CONFLICT DO NOTHING;
    INSERT INTO product_size VALUES(3, 'Large') ON CONFLICT DO NOTHING;
    """

COMMON_WORDS_FILE = Path(__file__).with_name("common_words.txt")


def load_common_words() -> list[str]:
    """1000 common English words, used to generate fake brand and product names."""
    return COMMON_WORDS_FILE.read_text().split()

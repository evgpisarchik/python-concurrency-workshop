-- Runs once, on the first start of the container.
-- The `products` schema and data are created by chapter 5 scripts
-- (02_create_schema, 04_insert_random_brands, 05_insert_random_products_and_skus).
CREATE DATABASE products;
CREATE DATABASE cart;
CREATE DATABASE favorites;

-- Listing 10.2: the cart service database
\c cart
CREATE TABLE user_cart(
    user_id    INT NOT NULL,
    product_id INT NOT NULL
);
INSERT INTO user_cart VALUES (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 5);

-- Listing 10.3: the favorites service database
\c favorites
CREATE TABLE user_favorite(
    user_id    INT NOT NULL,
    product_id INT NOT NULL
);
INSERT INTO user_favorite VALUES (1, 1), (1, 2), (1, 3), (3, 1), (3, 2), (3, 3);

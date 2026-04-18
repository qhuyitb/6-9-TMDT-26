-- 1. Bảng users [cite: 30, 31, 32]
-- Lưu tài khoản đăng nhập và trạng thái của cả khách hàng lẫn quản trị viên.
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(255) NULL,
    role ENUM('customer','admin') NOT NULL DEFAULT 'customer',
    status ENUM('active','locked','inactive') NOT NULL DEFAULT 'active',
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- 2. Bảng categories [cite: 36, 37, 38]
-- Lưu danh mục sản phẩm để hỗ trợ tìm kiếm, lọc và quản trị.
CREATE TABLE categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    slug VARCHAR(170) UNIQUE NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- 3. Bảng products [cite: 39, 40, 41]
-- Lưu thông tin sản phẩm điện tử, giá bán, tồn kho và trạng thái kinh doanh.
CREATE TABLE products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    category_id BIGINT NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(120) NOT NULL,
    price DECIMAL(12,2) NOT NULL CHECK (price >= 0),
    stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    description TEXT NULL,
    specifications TEXT NULL,
    business_status ENUM('active','inactive','discontinued') NOT NULL DEFAULT 'active',
    rating_average DECIMAL(3,2) NOT NULL DEFAULT 0.00,
    review_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 4. Bảng user_addresses [cite: 33, 34, 35]
-- Quản lý địa chỉ nhận hàng của khách hàng để phục vụ checkout và lịch sử đơn.
CREATE TABLE user_addresses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    receiver_name VARCHAR(150) NOT NULL,
    receiver_phone VARCHAR(20) NOT NULL,
    line1 VARCHAR(255) NOT NULL,
    ward VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 5. Bảng product_images [cite: 42, 43, 44]
-- Lưu nhiều ảnh cho một sản phẩm.
CREATE TABLE product_images (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INT NOT NULL DEFAULT 0,
    UNIQUE (product_id, sort_order),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 6. Bảng carts [cite: 45, 46, 47]
-- Lưu giỏ hàng đang hoạt động của khách hoặc người xem theo session.
CREATE TABLE carts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    session_id VARCHAR(100) UNIQUE NULL,
    status ENUM('active','checked_out','abandoned') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CHECK (user_id IS NOT NULL OR session_id IS NOT NULL),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 7. Bảng cart_items [cite: 48, 49, 50]
-- Chi tiết các sản phẩm có trong một giỏ hàng.
CREATE TABLE cart_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cart_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,
    UNIQUE (cart_id, product_id),
    FOREIGN KEY (cart_id) REFERENCES carts(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 8. Bảng wishlists [cite: 51, 52, 53]
-- Lưu danh sách yêu thích của khách hàng hoặc người xem theo session.
CREATE TABLE wishlists (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    session_id VARCHAR(100) UNIQUE NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CHECK (user_id IS NOT NULL OR session_id IS NOT NULL),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 9. Bảng wishlist_items [cite: 54, 55, 56]
-- Các sản phẩm cụ thể trong danh sách yêu thích.
CREATE TABLE wishlist_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    wishlist_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    added_at DATETIME NOT NULL,
    UNIQUE (wishlist_id, product_id),
    FOREIGN KEY (wishlist_id) REFERENCES wishlists(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 10. Bảng orders [cite: 57, 58, 59]
-- Lưu thông tin đơn hàng, trạng thái xử lý và trạng thái thanh toán.
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    address_id BIGINT NOT NULL,
    order_code VARCHAR(30) UNIQUE NOT NULL,
    order_date DATETIME NOT NULL,
    status ENUM('pending','confirmed','preparing','shipping','completed','cancelled') NOT NULL DEFAULT 'pending',
    payment_status ENUM('unpaid','pending','paid','failed','refunded','reconcile_pending') NOT NULL DEFAULT 'unpaid',
    shipping_method VARCHAR(100) NOT NULL,
    shipping_fee DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    subtotal_amount DECIMAL(12,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    cancel_reason VARCHAR(255) NULL,
    note TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (address_id) REFERENCES user_addresses(id)
);

-- 11. Bảng order_items [cite: 60, 61, 62]
-- Chi tiết từng sản phẩm trong một đơn hàng.
CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,
    line_total DECIMAL(12,2) NOT NULL,
    UNIQUE (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 12. Bảng payments [cite: 63, 64, 65]
-- Lưu giao dịch thanh toán online hoặc COD của đơn hàng.
CREATE TABLE payments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNIQUE NOT NULL,
    payment_method ENUM('cod','vnpay','momo','bank_transfer') NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status ENUM('pending','success','failed','cancelled','reconcile_pending') NOT NULL,
    transaction_ref VARCHAR(100) UNIQUE NULL,
    gateway_response TEXT NULL,
    paid_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- 13. Bảng reviews [cite: 66, 67, 68]
-- Lưu đánh giá sản phẩm của khách hàng đã mua.
CREATE TABLE reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    order_id BIGINT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NULL,
    review_date DATETIME NOT NULL,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
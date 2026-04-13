# 🛒 Website Quản Lý & Bán Thiết Bị Điện Tử

## 📌 Giới thiệu
Dự án xây dựng một website hỗ trợ:
- Quản lý sản phẩm điện tử
- Bán hàng online
- Quản lý đơn hàng
- Quản lý người dùng

---

## 🧑‍💻 Công nghệ sử dụng

### 🔹 Backend
- Python (Django / Flask)
- REST API

### 🔹 Frontend
- HTML, CSS, JavaScript
- Bootstrap

### 🔹 Cơ sở dữ liệu
- MySQL

### 🔹 Cổng thanh toán
- VNPAY
- PayPal
- Stripe

### 🔹 Vận chuyển
- GHN (Giao Hàng Nhanh)
- Viettel Post

### 🔹 Công cụ hỗ trợ
- Git: quản lý phiên bản, làm việc nhóm, tránh xung đột code
- Postman: kiểm thử API nhanh chóng
- Docker: đồng bộ môi trường phát triển và triển khai
- Visual Studio Code / PyCharm: môi trường lập trình Python

---

## ⚙️ Cài đặt môi trường Backend

### 1. Clone project
```bash
git clone <repo-url>
cd project
```

### 2. Tạo môi trường ảo
```bash
python -m venv venv
```

Kích hoạt:
```bash
venv\Scripts\activate   # Windows
```

---

### 3. Cài thư viện
```bash
pip install -r requirements.txt
```

---

### 4. Cấu hình database MySQL
```sql
CREATE DATABASE ecommerce_db;
```

---

### 5. Cấu hình biến môi trường (.env)
```
DB_NAME=ecommerce_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

---

### 6. Chạy project

#### Django
```bash
python manage.py migrate
python manage.py runserver
```

#### Flask
```bash
python app.py
```

---

## 📂 Cấu trúc thư mục

```
project/
├── frontend/
├── backend/
├── database/
├── docs/
└── README.md
```

---

# 🌿 Git Workflow & Quy tắc làm việc nhóm

## 1. Branch chính
- `main` → chứa code production (ổn định)
- `develop` → nhánh phát triển chính

---

## 2. Quy tắc đặt tên branch

```
feature/<ten-chuc-nang>
bugfix/<ten-loi>
hotfix/<ten-loi-nghiem-trong>
```

Ví dụ:
- feature/login
- feature/product-management
- bugfix/cart-error

---

## 3. Quy tắc bắt buộc

- ❌ Không push trực tiếp lên `main`
- ❌ Không push trực tiếp lên `develop`
- ❌ Không merge trực tiếp
- ✅ BẮT BUỘC sử dụng Pull Request (PR)
- ✅ Code phải được review trước khi merge

---

## 4. Quy trình làm việc

```bash
git checkout develop
git pull origin develop

git checkout -b feature/<ten-chuc-nang>

git add .
git commit -m "feat: add feature"

git push origin feature/<ten-chuc-nang>
```

---

## 5. Pull Request
- Tạo PR từ `feature/...` → `develop`
- Review code trước khi merge

---

## 👥 Thành viên nhóm
- Tô Quang Huy
- Doãn Đức Nghĩa
- Ngô Bá Đạt
- Phạm Thanh Bình
- Mai Xuân Nhân

---

## 🚀 Hướng phát triển
- Tích hợp thanh toán online
- Gợi ý sản phẩm bằng AI
- Tối ưu UX/UI
```
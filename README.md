# 🛒 Website Quản Lý & Bán Thiết Bị Điện Tử

## 📌 Giới thiệu

Dự án xây dựng một website hỗ trợ:

* Quản lý sản phẩm điện tử
* Bán hàng online
* Quản lý đơn hàng
* Quản lý người dùng

---

## 🧑‍💻 Công nghệ sử dụng

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

* `main` → chứa code production (ổn định)
* `develop` → nhánh phát triển chính

---

## 2. Quy tắc đặt tên branch

### 📌 Format:

```
feature/<ten-chuc-nang>
bugfix/<ten-loi>
hotfix/<ten-loi-nghiem-trong>
```

### 📌 Ví dụ:

* `feature/login`
* `feature/product-management`
* `bugfix/cart-error`
* `hotfix/payment-fail`

---

## 3. 🚫 Quy tắc bắt buộc

* ❌ Không push trực tiếp lên `main`

* ❌ Không push trực tiếp lên `develop`

* ❌ Không tự ý merge code

* ✅ BẮT BUỘC sử dụng **Pull Request (PR)**

* ✅ Code phải được review trước khi merge

---

## 4. 🔄 Quy trình làm việc

### Bước 1: Update code mới nhất

```
git checkout develop
git pull origin develop
```

---

### Bước 2: Tạo branch mới

```
git checkout -b feature/<ten-chuc-nang>
```

---

### Bước 3: Code & commit

```
git add .
git commit -m "feat: thêm chức năng đăng nhập"
```

### 📌 Quy ước commit:

* `feat:` thêm tính năng
* `fix:` sửa lỗi
* `update:` cập nhật
* `refactor:` tối ưu code
* `docs:` cập nhật tài liệu

---

### Bước 4: Push code

```
git push origin feature/<ten-chuc-nang>
```

---

### Bước 5: Tạo Pull Request

* Tạo PR từ `feature/...` → `develop`
* Mô tả rõ:

  * Làm gì
  * Screenshot (nếu có)
  * Cách test

---

### Bước 6: Code Review & Merge

* Ít nhất **1 thành viên review**
* Sau khi OK → merge vào `develop`

---

## 5. 🔥 Quy tắc merge

* Merge vào `develop` trước
* Test ổn định → mới merge `develop` → `main`

---

## 6. ⚠️ Lưu ý quan trọng

* Luôn `git pull` trước khi code
* Resolve conflict cẩn thận
* Không commit file rác (`node_modules`, `.env`, ...)

---

## 👥 Thành viên nhóm

* Thành viên 1: Tô Quang Huy
* Thành viên 2: Doãn Đức Nghĩa
* Thành viên 3: Ngô Bá Đạt
* Thành viên 4: Phạm Thanh Bình
* Thành viên 5: Mai Xuân Nhân

---

## 🚀 Hướng phát triển

* Tích hợp thanh toán online
* Gợi ý sản phẩm bằng AI
* Tối ưu UX/UI

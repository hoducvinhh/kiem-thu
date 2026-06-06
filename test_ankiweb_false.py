# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import unittest
# import time

# class TestAnkiRegisterValidation(unittest.TestCase):

#     def setUp(self):
#         # Hàm này tự động chạy TRƯỚC mỗi test case để khởi tạo trình duyệt mới
#         self.driver = webdriver.Chrome()
#         self.driver.maximize_window()
#         self.wait = WebDriverWait(self.driver, 10)

#     def test_01_signup_button_disabled_with_invalid_char(self):
#         """Test Case 1: Email chứa ký tự đặc biệt % phải bị disable nút Sign Up"""
#         driver = self.driver
        
#         # 1. Truy cập trang đăng ký AnkiWeb
#         driver.get("https://ankiweb.net/account/signup")
        
#         # 2. Định vị các phần tử trên trang
#         email_input = self.wait.until(
#             EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email' or @type='email']"))
#         )
#         password_input = driver.find_element(By.XPATH, "//input[@placeholder='New Password' or @type='password']")
#         signup_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign Up')]")

#         # 3. Nhập dữ liệu lỗi (Email chứa ký tự %)
#         invalid_email = "test%user@gmail.com"
#         password_input.send_keys("SecurePass123!")
#         email_input.send_keys(invalid_email)
        
#         # Chờ 1.5 giây để giao diện cập nhật trạng thái nút
#         time.sleep(1.5)

#         # 4. Kiểm tra xem nút Sign Up có bị disable hay không
#         is_button_enabled = signup_button.is_enabled()
#         has_disabled_attribute = signup_button.get_attribute("disabled") is not None
#         is_button_disabled = (not is_button_enabled) or has_disabled_attribute
        
#         print(f"\n[Test 1] Nút Sign Up có bị disable khi email chứa '%' không? -> {is_button_disabled}")

#         # Assert: Nếu không bị disable -> Trả về False (Failed)
#         self.assertTrue(is_button_disabled, "False: Nút Sign Up không bị disable dù email chứa ký tự '%' không hợp lệ!")

#     def test_02_signup_button_disabled_with_non_gmail(self):
#         """Test Case 2: Email không phải đuôi @gmail.com (ví dụ @b.abc) phải bị disable nút Sign Up"""
#         driver = self.driver
        
#         # 1. Truy cập trang đăng ký AnkiWeb
#         driver.get("https://ankiweb.net/account/signup")
        
#         # 2. Định vị các phần tử trên trang
#         email_input = self.wait.until(
#             EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email' or @type='email']"))
#         )
#         password_input = driver.find_element(By.XPATH, "//input[@placeholder='New Password' or @type='password']")
#         signup_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign Up')]")

#         # 3. Nhập email có đuôi khác @gmail.com (Ví dụ: testuser@b.abc)
#         non_gmail_email = "testuser@b.abc"
#         password_input.send_keys("SecurePass123!")
#         email_input.send_keys(non_gmail_email)
        
#         # Chờ 1.5 giây để giao diện cập nhật trạng thái nút
#         time.sleep(1.5)

#         # 4. Kiểm tra xem nút Sign Up có bị disable hay không
#         is_button_enabled = signup_button.is_enabled()
#         has_disabled_attribute = signup_button.get_attribute("disabled") is not None
#         is_button_disabled = (not is_button_enabled) or has_disabled_attribute
        
#         print(f"\n[Test 2] Nút Sign Up có bị disable khi đuôi email là '@b.abc' không? -> {is_button_disabled}")

#         # Assert: Nếu không bị disable -> Trả về False (Failed) đúng ý bạn
#         self.assertTrue(is_button_disabled, "False: Nút Sign Up vẫn cho phép bấm dù đuôi email không phải là @gmail.com!")

#     def tearDown(self):
#         # Hàm này tự động chạy SAU mỗi test case để đóng trình duyệt
#         self.driver.quit()

# if __name__ == "__main__":
#     unittest.main()




from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import unittest
import time


def load_local_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


class TestAnkiRegisterValidation(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)

    def test_01_signup_button_disabled_with_invalid_char(self):
        """Test Case 1: Email chứa ký tự đặc biệt % phải bị disable nút Sign Up"""
        driver = self.driver
        driver.get("https://ankiweb.net/account/signup")
        
        email_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email' or @type='email']"))
        )
        password_input = driver.find_element(By.XPATH, "//input[@placeholder='New Password' or @type='password']")
        signup_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign Up')]")

        invalid_email = "test%user@gmail.com"
        password_input.send_keys("SecurePass123!")
        email_input.send_keys(invalid_email)
        
        time.sleep(1.5)

        is_button_enabled = signup_button.is_enabled()
        has_disabled_attribute = signup_button.get_attribute("disabled") is not None
        is_button_disabled = (not is_button_enabled) or has_disabled_attribute
        
        print(f"\n[Test 1] Nút Sign Up có bị disable khi email chứa '%' không? -> {is_button_disabled}")
        self.assertTrue(is_button_disabled, "False: Nút Sign Up không bị disable dù email chứa ký tự '%' không hợp lệ!")

    def test_02_signup_button_disabled_with_non_gmail(self):
        """Test Case 2: Email không phải đuôi @gmail.com (ví dụ @b.abc) phải bị disable nút Sign Up"""
        driver = self.driver
        driver.get("https://ankiweb.net/account/signup")
        
        email_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email' or @type='email']"))
        )
        password_input = driver.find_element(By.XPATH, "//input[@placeholder='New Password' or @type='password']")
        signup_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign Up')]")

        non_gmail_email = "testuser@b.abc"
        password_input.send_keys("SecurePass123!")
        email_input.send_keys(non_gmail_email)
        
        time.sleep(1.5)

        is_button_enabled = signup_button.is_enabled()
        has_disabled_attribute = signup_button.get_attribute("disabled") is not None
        is_button_disabled = (not is_button_enabled) or has_disabled_attribute
        
        print(f"\n[Test 2] Nút Sign Up có bị disable khi đuôi email là '@b.abc' không? -> {is_button_disabled}")
        self.assertTrue(is_button_disabled, "False: Nút Sign Up vẫn cho phép bấm dù đuôi email không phải là @gmail.com!")

    def test_03_logout_and_back_button_cache_leak(self):
        """Test Case 3: Đăng xuất xong bấm Back nếu còn nhìn thấy chữ 'Decks' thì trả về False"""
        driver = self.driver
        
        # --- BƯỚC 1: ĐĂNG NHẬP VÀO HỆ THỐNG ---
        driver.get("https://ankiweb.net/account/login")
        self.wait.until(EC.url_contains("login"))
        
        email_input = self.wait.until(EC.element_to_be_clickable((By.ID, "email")))
        password_input = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
        
        # ⚠️ Hãy điền tài khoản thật hoạt động được của bạn ở đây:
        email_input.send_keys("taikhoanthuclogin@gmail.com")
        password_input.send_keys("MatKhauCuaBan123!")
        login_button.click()
        
        # Đợi cho đến khi vào được trang Dashboard (có chữ Decks hoặc nút Log Out hiển thị)
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Log Out') or contains(text(), 'Logout')]")))
        print("\n[Test 3] Đăng nhập thành công, đã vào giao diện thành viên.")

        # --- BƯỚC 2: THỰC HIỆN ĐĂNG XUẤT ---
        logout_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Log Out') or contains(text(), 'Logout')]")
        logout_button.click()
        
        # Chờ quay trở lại màn hình đăng nhập sạch
        self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        print("[Test 3] Đã bấm Log Out thành công.")
        time.sleep(2.0)

        # --- BƯỚC 3: BẤM NÚT BACK TRÊN TRÌNH DUYỆT ---
        print("[Test 3] Thực hiện bấm nút BACK trên trình duyệt...")
        driver.back()
        time.sleep(2.5)  # Chờ trình duyệt lấy dữ liệu hiển thị từ Cache (nếu lỗi)

        # --- BƯỚC 4: KIỂM TRA DUY NHẤT CHỮ 'DECKS' ---
        # Tìm tất cả phần tử chứa chữ 'Decks' công khai trên màn hình
        decks_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Decks')]")
        
        # Kiểm tra xem có phần tử nào đang thực sự hiển thị (is_displayed) hay không
        is_decks_visible = len(decks_elements) > 0 and any(elem.is_displayed() for elem in decks_elements)
        
        print(f"[Test 3] Sau khi Back, có còn nhìn thấy chữ 'Decks' trên màn hình không? -> {is_decks_visible}")

        # Assert logic: 
        # Nếu nhìn thấy chữ Decks (True) -> Kích hoạt lỗi AssertionError: False is not true (Bài test bị Failed)
        self.assertFalse(
            is_decks_visible, 
            "False: Lỗi Cache Giao diện! Sau khi Logout và bấm Back, màn hình vẫn hiển thị chữ 'Decks'!"
        )

    @unittest.skipUnless(
        os.getenv("ANKI_EMAIL") and os.getenv("ANKI_PASSWORD"),
        "Set ANKI_EMAIL and ANKI_PASSWORD to run this authenticated test.",
    )
    def test_03_logout_and_back_button_cache_leak(self):
        """After logout, browser Back must not expose the authenticated account UI."""
        email = os.getenv("ANKI_EMAIL")
        password = os.getenv("ANKI_PASSWORD")
        if not email or not password:
            self.skipTest("Set ANKI_EMAIL and ANKI_PASSWORD to run this authenticated test.")

        driver = self.driver

        driver.get("https://ankiweb.net/account/login")
        self.wait.until(EC.url_contains("login"))

        email_input = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//input[@type='email' or contains(@placeholder, 'Email') "
                    "or contains(@name, 'email') or contains(@id, 'email')]",
                )
            )
        )
        password_input = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//input[@type='password' or contains(@placeholder, 'Password') "
                    "or contains(@name, 'password') or contains(@id, 'password')]",
                )
            )
        )
        login_button_locator = (
            By.XPATH,
            "//*[self::button or self::input]"
            "[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') "
            "or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') "
            "or @type='submit']",
        )
        self.wait.until(EC.presence_of_element_located(login_button_locator))

        email_input.send_keys(email)
        password_input.send_keys(password)
        login_button = self.wait.until(EC.element_to_be_clickable(login_button_locator))
        login_button.click()

        logout_locator = (
            By.XPATH,
            "//a[contains(@href, '/account/logout') or contains(., 'Log Out') or contains(., 'Logout')]",
        )
        logout_button = self.wait.until(EC.element_to_be_clickable(logout_locator))
        print("\n[Test 3] Login succeeded.")

        logout_button.click()
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//input[@type='email' or contains(@placeholder, 'Email') "
                    "or contains(@name, 'email') or contains(@id, 'email')]",
                )
            )
        )
        print("[Test 3] Logout succeeded.")

        driver.back()
        time.sleep(1.5)

        authenticated_elements = driver.find_elements(
            By.XPATH,
            "//*[contains(@href, '/account/logout') "
            "or contains(., 'Log Out') "
            "or contains(., 'Logout') "
            "or contains(., 'Create Deck')]",
        )
        is_authenticated_ui_visible = any(element.is_displayed() for element in authenticated_elements)

        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@type='email' or contains(@placeholder, 'Email') "
                        "or contains(@name, 'email') or contains(@id, 'email')]",
                    )
                )
            )
            login_form_visible = True
        except TimeoutException:
            login_form_visible = False

        print(f"[Test 3] Authenticated UI visible after Back? -> {is_authenticated_ui_visible}")
        print(f"[Test 3] Login form visible after Back? -> {login_form_visible}")

        self.assertFalse(
            is_authenticated_ui_visible,
            "False: cache leak. After logout and browser Back, authenticated UI is still visible.",
        )
        self.assertTrue(login_form_visible, "Expected the login form to be visible after logout and Back.")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()

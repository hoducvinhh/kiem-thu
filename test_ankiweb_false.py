from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest
import time

class TestAnkiRegister(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)

    def test_signup_button_disabled_with_invalid_email(self):
        driver = self.driver
        
        # 1. Truy cập trang đăng ký AnkiWeb
        driver.get("https://ankiweb.net/account/signup")
        
        # 2. Tìm ô nhập bằng placeholder hiển thị trên giao diện của bạn
        email_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email' or @type='email']"))
        )
        password_input = driver.find_element(By.XPATH, "//input[@placeholder='New Password' or @type='password']")
        
        # Tìm nút Sign Up (Nút màu xanh chữ trắng)
        signup_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign Up')]")

        # 3. Nhập dữ liệu lỗi (Email chứa ký tự %)
        invalid_email = "test%user@gmail.com"
        password_input.send_keys("SecurePass123!")
        email_input.send_keys(invalid_email)
        
        # Chờ 1.5 giây để giao diện cập nhật trạng thái nút
        time.sleep(1.5)

        # 4. Kiểm tra xem nút Sign Up có thực sự bị disable hay không
        is_button_enabled = signup_button.is_enabled()
        has_disabled_attribute = signup_button.get_attribute("disabled") is not None
        
        is_button_disabled = (not is_button_enabled) or has_disabled_attribute
        
        print(f"\n[Trạng thái thực tế] Nút Sign Up có bị disable không? -> {is_button_disabled}")

        # LOGIC: 
        # Nếu bị disable (True) -> PASSED
        # Nếu KHÔNG bị disable (False) -> FAILED (Trả về False/AssertionError đúng ý bạn)
        self.assertTrue(is_button_disabled, "False: Nút Sign Up không bị disable dù email chứa ký tự '%' không hợp lệ!")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
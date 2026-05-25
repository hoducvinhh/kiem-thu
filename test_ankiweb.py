import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def open_browser():
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver

# ==============================================================================
# PHẦN 1: KIỂM THỬ CHỨC NĂNG ĐĂNG NHẬP (LOGIN)
# ==============================================================================

# 1. Test đăng nhập THÀNH CÔNG
def test_login_success():
    driver = open_browser()
    driver.get("https://ankiweb.net/account/login")

    # Điền Email 
    email_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email']"))
    )
    email_input.send_keys("hoducvinh2k4@gmail.com") 

    # Điền Mật khẩu 
    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys("vinhhoa12345")
    password_input.send_keys(Keys.ENTER)

    # KỲ VỌNG: Đăng nhập thành công xuất hiện nút đăng xuất
    logout_button = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Log Out') or contains(text(), 'Sign Out')]"))
    )
    
    assert logout_button.is_displayed()
    driver.quit()


# 2. Test đăng nhập THẤT BẠI (Sai mật khẩu)
def test_login_fail_wrong_password():
    driver = open_browser()
    driver.get("https://ankiweb.net/account/login")

    # Điền Email
    email_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email']"))
    )
    email_input.send_keys("hoducvinh2k4@gmail.com")

    # Điền Mật khẩu sai
    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys("SaiMatKhauHoanToan123")
    password_input.send_keys(Keys.ENTER)

    # KỲ VỌNG: Hệ thống hiển thị thông báo lỗi chứa chữ "does not match our records"
    error_message = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'does not match our records')]"))
    )

    assert error_message.is_displayed()
    assert "account/login" in driver.current_url  
    driver.quit()


# ==============================================================================
# PHẦN 2: KIỂM THỬ CHỨC NĂNG ĐĂNG KÝ (SIGNUP)
# ==============================================================================

# 3. Test đăng ký THẤT BẠI (Email sai định dạng)
def test_signup_fail_invalid_email():
    driver = open_browser()
    driver.get("https://ankiweb.net/account/signup")

    # Nhập email thiếu đuôi @gmail.com
    email_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email']"))
    )
    email_input.send_keys("email_sai_dinh_dang")

    # Nhập password bừa
    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys("Password123!")
    password_input.send_keys(Keys.ENTER)

    # KỲ VỌNG: Hệ thống giữ lại ở trang signup do lỗi định dạng
    time.sleep(2) 
    assert "account/signup" in driver.current_url
    driver.quit()


# 4. Test đăng ký THÀNH CÔNG (Sử dụng Email sinh ngẫu nhiên theo thời gian)
def test_signup_success_dynamic():
    driver = open_browser()
    driver.get("https://ankiweb.net/account/signup")

    timestamp = int(time.time())
    unique_email = f"ankitest_{timestamp}@gmail.com"

    # Điền Email ngẫu nhiên vừa tạo
    email_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email']"))
    )
    email_input.send_keys(unique_email)

    # Điền Mật khẩu hợp lệ
    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys("MatKhauManh2026!")
    password_input.send_keys(Keys.ENTER)

    # KỲ VỌNG: Chuyển hướng sang trang điều khoản (Terms) hoặc thông báo Confirm
    success_page_element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Terms') or contains(text(), 'Email sent') or contains(text(), 'Confirm')]"))
    )

    assert success_page_element.is_displayed()
    driver.quit()


# ==============================================================================
# PHẦN 3: KIỂM THỬ CHỨC NĂNG TÌM KIẾM VÀ TRUY CẬP CHIA SẺ (SHARED DECKS)
# ==============================================================================

# 5. Test chức năng TÌM KIẾM bộ thẻ chia sẻ thật công khai
def test_search_shared_deck_real():
    driver = open_browser()
    driver.get("https://ankiweb.net/shared/decks")

    # 1. Định vị ô tìm kiếm bằng input text/search trên trang chia sẻ công đồng
    search_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='search']"))
    )
    
    search_box.clear()
    search_box.send_keys("english")
    search_box.send_keys(Keys.ENTER)

    # 2. KỲ VỌNG: Kết quả tìm kiếm phải hiển thị các bộ thẻ có chứa tiêu đề tương ứng
    first_result = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'English') or contains(text(), 'english')]"))
    )

    assert first_result.is_displayed()
    assert "decks" in driver.current_url or "search" in driver.current_url
    driver.quit()


# 6. Test chức năng TÌM KIẾM & TRUY CẬP bộ thẻ sau khi ĐÃ ĐĂNG NHẬP (BẢN TỐI ƯU CLICK)
def test_view_shared_deck_detail_real():
    driver = open_browser()
    
    # BƯỚC 1: ĐĂNG NHẬP TRƯỚC
    driver.get("https://ankiweb.net/account/login")
    email_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email']"))
    )
    email_input.send_keys("hoducvinh2k4@gmail.com") 

    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys("vinhhoa12345")
    password_input.send_keys(Keys.ENTER)

    # Đợi đăng nhập thành công
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Log Out') or contains(text(), 'Sign Out')]"))
    )

    # BƯỚC 2: QUAY TRỞ LẠI TRANG SHARED DECKS QUA MENU
    shared_decks_menu = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/shared/decks') or contains(text(), 'Shared')]"))
    )
    shared_decks_menu.click()

    # BƯỚC 3: TIẾN HÀNH TÌM KIẾM
    search_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='search']"))
    )
    search_box.clear()
    search_box.send_keys("english")
    search_box.send_keys(Keys.ENTER)

    # BƯỚC 4: CLICK VÀO BỘ THẺ ĐẦU TIÊN QUA ĐƯỜNG DẪN INFO CHUẨN
    # Sử dụng XPATH lọc chính xác thẻ <a> chứa '/shared/info/' để không bị click nhầm menu
    first_deck_link = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "(//a[contains(@href, '/shared/info/')])[1]"))
    )
    first_deck_link.click()

    # Đợi tối đa 10 giây cho đến khi URL thực sự chuyển hướng sang trang chi tiết
    WebDriverWait(driver, 10).until(
        EC.url_contains("/shared/info/")
    )

    # KỲ VỌNG (ASSERT): Xác thực lại URL một lần nữa để kết thúc bài test thành công
    assert "/shared/info/" in driver.current_url, f"Lỗi: Trình duyệt đang kẹt ở URL: {driver.current_url}"
    
    driver.quit()
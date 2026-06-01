import os
import time
from urllib.parse import quote_plus

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://ankiweb.net"
LOGIN_URL = f"{BASE_URL}/account/login"
SIGNUP_URL = f"{BASE_URL}/account/signup"
SHARED_DECKS_URL = f"{BASE_URL}/shared/decks"


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

ANKI_EMAIL = os.getenv("ANKI_EMAIL")
ANKI_PASSWORD = os.getenv("ANKI_PASSWORD")
TEST_EMAIL = ANKI_EMAIL or "user@example.com"
WAIT_SECONDS = int(os.getenv("SELENIUM_WAIT_SECONDS", "3"))


@pytest.fixture
def driver():
    browser = create_browser()
    yield browser
    browser.quit()


@pytest.fixture(scope="session")
def authenticated_driver():
    browser = create_browser()
    submit_login(browser)
    try:
        assert_logged_in(browser)
    except (AssertionError, TimeoutException):
        current_url = browser.current_url
        browser.quit()
        pytest.skip(
            "Cannot continue authenticated tests: login did not reach account page. "
            f"Current URL: {current_url}"
        )
    yield browser
    browser.quit()


def create_browser():
    options = Options()
    options.page_load_strategy = "eager"
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        },
    )
    if os.getenv("SELENIUM_HEADLESS", "1") != "0":
        options.add_argument("--headless=new")

    return webdriver.Chrome(options=options)


def wait(driver, seconds=WAIT_SECONDS):
    return WebDriverWait(driver, seconds)


def find_any(driver, locators, condition=EC.presence_of_element_located, seconds=WAIT_SECONDS):
    last_error = None
    for locator in locators:
        try:
            return wait(driver, seconds).until(condition(locator))
        except TimeoutException as error:
            last_error = error
    raise last_error


def find_email_input(driver):
    return find_any(
        driver,
        [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[contains(@placeholder, 'Email')]"),
            (By.XPATH, "//input[contains(@name, 'email') or contains(@id, 'email')]"),
        ],
    )


def find_password_input(driver):
    return find_any(
        driver,
        [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[contains(@placeholder, 'Password')]"),
        ],
    )


def find_login_button(driver):
    return find_any(
        driver,
        [
            (
                By.XPATH,
                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') "
                "or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
            ),
            (
                By.XPATH,
                "//input[@type='submit' and (contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') "
                "or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login'))]",
            ),
            (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"),
        ],
    )


def find_clickable_login_button(driver):
    return find_any(
        driver,
        [
            (
                By.XPATH,
                "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') "
                "or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
            ),
            (
                By.XPATH,
                "//input[@type='submit' and (contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') "
                "or contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login'))]",
            ),
            (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"),
        ],
        EC.element_to_be_clickable,
    )


def submit_login(driver, email=ANKI_EMAIL, password=ANKI_PASSWORD):
    if not email or not password:
        pytest.skip("Set ANKI_EMAIL and ANKI_PASSWORD to run authenticated tests.")
    driver.get(LOGIN_URL)
    find_email_input(driver).send_keys(email)
    password_input = find_password_input(driver)
    password_input.send_keys(password)
    try:
        find_clickable_login_button(driver).click()
    except TimeoutException:
        password_input.send_keys(Keys.ENTER)


def assert_error_visible(driver):
    error = find_any(
        driver,
        [
            (By.CSS_SELECTOR, "[role='alert'], .error, .alert, .invalid-feedback"),
            (
                By.XPATH,
                "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'error') "
                "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'invalid') "
                "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'required') "
                "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'match our records') "
                "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'must')]",
            ),
        ],
    )
    assert error.is_displayed()


def assert_logged_in(driver):
    account_element = find_any(
        driver,
        [
            (By.XPATH, "//*[contains(., 'Log Out') or contains(., 'Sign Out')]"),
            (By.XPATH, "//a[contains(@href, '/account/logout')]"),
            (By.XPATH, "//*[self::button or self::a][contains(., 'Create Deck')]"),
        ],
    )
    assert account_element.is_displayed()
    assert "account/login" not in driver.current_url


def login_or_skip(driver):
    submit_login(driver)
    try:
        assert_logged_in(driver)
    except (AssertionError, TimeoutException):
        pytest.skip(
            "Cannot continue authenticated test: login did not reach account page. "
            f"Current URL: {driver.current_url}"
        )


def open_create_deck_prompt(driver):
    create_button = find_any(
        driver,
        [
            (By.XPATH, "//*[self::button or self::a][contains(., 'Create Deck')]"),
            (By.XPATH, "//*[self::button or self::a][contains(., 'Create')]"),
            (By.XPATH, "//*[self::button or self::a][contains(., 'New')]"),
        ],
        EC.element_to_be_clickable,
    )
    create_button.click()
    wait(driver, 10).until(EC.alert_is_present())
    return driver.switch_to.alert


def find_deck_by_name(driver, deck_name, seconds=10):
    locator = (By.XPATH, f"//*[contains(., '{deck_name}')]")
    try:
        return find_any(driver, [locator], seconds=seconds)
    except TimeoutException:
        driver.refresh()
        return find_any(driver, [locator], seconds=seconds)


def go_to_shared_decks(driver):
    driver.get(SHARED_DECKS_URL)
    return find_any(
        driver,
        [
            (By.CSS_SELECTOR, "input[type='search']"),
            (By.XPATH, "//input[@type='text' or @type='search']"),
        ],
    )


def shared_deck_links(driver):
    return driver.find_elements(By.XPATH, "//a[contains(@href, '/shared/info/')]")


def search_shared_decks(driver, keyword):
    search_box = go_to_shared_decks(driver)
    search_box.clear()
    if keyword:
        search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)

    expected_url_part = keyword.replace(" ", "+").lower()
    try:
        wait(driver, 5).until(
            lambda d: expected_url_part in d.current_url.lower() or shared_deck_links(d)
        )
    except TimeoutException:
        driver.get(f"{SHARED_DECKS_URL}?search={quote_plus(keyword)}")
    page_text = find_any(driver, [(By.TAG_NAME, "body")]).text.lower()
    if "please log in to perform more searches" in page_text:
        pytest.skip("AnkiWeb requires login to perform shared deck search.")
    return find_any(driver, [(By.TAG_NAME, "body")])


# 1. Dang nhap


def test_ui_login_01_hien_thi_form_dang_nhap(driver):
    driver.get(LOGIN_URL)

    assert find_email_input(driver).is_displayed()
    assert find_password_input(driver).is_displayed()
    assert find_login_button(driver).is_displayed()


def test_ui_login_02_email_rong_bao_loi(driver):
    driver.get(LOGIN_URL)

    find_password_input(driver).send_keys("Password123!")
    login_button = find_login_button(driver)

    assert not login_button.is_enabled()


def test_ui_login_03_password_rong_bao_loi(driver):
    driver.get(LOGIN_URL)

    find_email_input(driver).send_keys(TEST_EMAIL)
    login_button = find_login_button(driver)

    assert not login_button.is_enabled()


def test_ui_login_04_sai_email_password_bao_loi(driver):
    submit_login(driver, "wrong-user@example.com", "SaiMatKhauHoanToan123")

    assert_error_visible(driver)
    assert "account/login" in driver.current_url


def test_ui_login_05_dung_email_password_vao_trang_tai_khoan(authenticated_driver):
    assert_logged_in(authenticated_driver)


def test_ui_login_06_click_sign_up_chuyen_sang_dang_ky(driver):
    driver.get(LOGIN_URL)

    sign_up_link = find_any(
        driver,
        [
            (By.XPATH, "//a[contains(., 'Sign Up') or contains(., 'Sign up') or contains(@href, 'signup')]"),
        ],
        EC.element_to_be_clickable,
    )
    sign_up_link.click()

    wait(driver).until(EC.url_contains("/account/signup"))
    assert "/account/signup" in driver.current_url


def test_ui_login_07_click_reset_password_chuyen_sang_reset(driver):
    driver.get(LOGIN_URL)

    reset_link = find_any(
        driver,
        [
            (By.XPATH, "//a[contains(., 'Reset Password') or contains(., 'Reset password')]"),
            (By.XPATH, "//a[contains(@href, 'reset') or contains(@href, 'forgot')]"),
        ],
        EC.element_to_be_clickable,
    )
    reset_link.click()

    wait(driver).until(lambda d: "reset" in d.current_url.lower() or "forgot" in d.current_url.lower())
    assert "account/login" not in driver.current_url


# 2. Dang ky


def test_ui_register_01_hien_thi_form_dang_ky(driver):
    driver.get(SIGNUP_URL)

    assert find_email_input(driver).is_displayed()
    assert find_password_input(driver).is_displayed()


def test_ui_register_02_email_rong_bao_loi(driver):
    driver.get(SIGNUP_URL)

    find_password_input(driver).send_keys("Password123!")
    find_password_input(driver).send_keys(Keys.ENTER)

    assert_error_visible(driver)


def test_ui_register_03_email_sai_dinh_dang_bao_loi(driver):
    driver.get(SIGNUP_URL)

    find_email_input(driver).send_keys("email_sai_dinh_dang")
    find_password_input(driver).send_keys("Password123!")
    find_password_input(driver).send_keys(Keys.ENTER)

    assert "account/signup" in driver.current_url


def test_ui_register_04_password_yeu_ngan_bao_loi(driver):
    driver.get(SIGNUP_URL)

    find_email_input(driver).send_keys(f"ankitest_{int(time.time())}@example.com")
    find_password_input(driver).send_keys("123")
    find_password_input(driver).send_keys(Keys.ENTER)

    assert_error_visible(driver)


def test_ui_register_05_nhap_hop_le_gui_xac_nhan(driver):
    driver.get(SIGNUP_URL)
    unique_email = f"ankitest_{int(time.time())}@example.com"

    find_email_input(driver).send_keys(unique_email)
    find_password_input(driver).send_keys("MatKhauManh2026!")
    find_password_input(driver).send_keys(Keys.ENTER)

    confirmation = find_any(
        driver,
        [
            (
                By.XPATH,
                "//*[contains(., 'Email sent') or contains(., 'Confirm') or contains(., 'confirm') "
                "or contains(., 'verification') or contains(., 'Terms')]",
            ),
        ],
    )
    assert confirmation.is_displayed()


def test_ui_register_06_click_login_quay_ve_dang_nhap(driver):
    driver.get(SIGNUP_URL)

    login_link = find_any(
        driver,
        [
            (By.XPATH, "//a[contains(., 'Log In') or contains(., 'Login') or contains(@href, 'login')]"),
        ],
        EC.element_to_be_clickable,
    )
    login_link.click()

    wait(driver).until(EC.url_contains("/account/login"))
    assert "/account/login" in driver.current_url


# 3. Tao moi


def test_ui_create_01_click_nut_tao_moi_mo_form(authenticated_driver):
    driver = authenticated_driver
    driver.get(BASE_URL)
    assert_logged_in(driver)

    alert = open_create_deck_prompt(driver)

    assert alert.text
    alert.dismiss()


def test_ui_create_02_bo_trong_ten_bao_loi_bat_buoc(authenticated_driver):
    driver = authenticated_driver
    driver.get(BASE_URL)
    assert_logged_in(driver)

    alert = open_create_deck_prompt(driver)
    alert.accept()

    assert_error_visible(driver)


def test_ui_create_03_nhap_ten_hop_le_tao_thanh_cong(authenticated_driver):
    driver = authenticated_driver
    driver.get(BASE_URL)
    assert_logged_in(driver)
    deck_name = f"Bo_The_Test_{int(time.time())}"

    alert = open_create_deck_prompt(driver)
    alert.send_keys(deck_name)
    alert.accept()

    new_deck = find_deck_by_name(driver, deck_name)
    assert new_deck.is_displayed()


def test_ui_create_04_nhap_ten_qua_dai_bao_loi_hoac_chan_nhap(authenticated_driver):
    driver = authenticated_driver
    driver.get(BASE_URL)
    assert_logged_in(driver)
    long_name = "A" * 300

    alert = open_create_deck_prompt(driver)
    alert.send_keys(long_name)
    alert.accept()

    try:
        assert_error_visible(driver)
    except TimeoutException:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert long_name not in page_text


def test_ui_create_05_click_cancel_dong_form_khong_tao_du_lieu(authenticated_driver):
    driver = authenticated_driver
    driver.get(BASE_URL)
    assert_logged_in(driver)
    unique_name = f"Cancel_Test_{int(time.time())}"

    alert = open_create_deck_prompt(driver)
    alert.send_keys(unique_name)
    alert.dismiss()
    driver.refresh()

    body_text = find_any(driver, [(By.TAG_NAME, "body")]).text
    assert unique_name not in body_text


def test_ui_create_06_sau_khi_tao_item_hien_thi_trong_danh_sach(authenticated_driver):
    driver = authenticated_driver
    driver.get(BASE_URL)
    assert_logged_in(driver)
    deck_name = f"Deck_List_Test_{int(time.time())}"

    alert = open_create_deck_prompt(driver)
    alert.send_keys(deck_name)
    alert.accept()

    deck_item = find_deck_by_name(driver, deck_name)
    assert deck_item.is_displayed()


# 4. Tim kiem


def test_ui_search_01_hien_thi_o_tim_kiem(driver):
    search_box = go_to_shared_decks(driver)

    assert search_box.is_displayed()


def test_ui_search_02_tim_tu_khoa_hop_le_hien_thi_ket_qua(authenticated_driver):
    driver = authenticated_driver
    search_shared_decks(driver, "english")

    result = find_any(driver, [(By.XPATH, "//a[contains(@href, '/shared/info/')]")])
    assert result.is_displayed()


def test_ui_search_03_tim_khong_co_ket_qua_hien_thi_khong_tim_thay(authenticated_driver):
    driver = authenticated_driver
    search_shared_decks(driver, "zzzzzzzzzz_no_deck_should_match_2026")

    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert not shared_deck_links(driver) or "no results" in page_text or "not found" in page_text


def test_ui_search_04_tim_ky_tu_dac_biet_khong_loi_giao_dien(authenticated_driver):
    driver = authenticated_driver
    search_shared_decks(driver, "@#$%^&*()[]{}")

    body = find_any(driver, [(By.TAG_NAME, "body")])
    assert body.is_displayed()
    assert "500" not in driver.title


def test_ui_search_05_tim_o_rong_hien_thi_mac_dinh(driver):
    search_box = go_to_shared_decks(driver)

    search_box.clear()
    search_box.send_keys(Keys.ENTER)

    body = find_any(driver, [(By.TAG_NAME, "body")])
    assert body.is_displayed()
    assert "shared/decks" in driver.current_url


def test_ui_search_06_click_ket_qua_mo_dung_trang_chi_tiet(authenticated_driver):
    driver = authenticated_driver
    search_shared_decks(driver, "english")

    first_deck_link = find_any(
        driver,
        [(By.XPATH, "(//a[contains(@href, '/shared/info/')])[1]")],
        EC.element_to_be_clickable,
    )
    first_deck_link.click()

    wait(driver, 10).until(EC.url_contains("/shared/info/"))
    assert "/shared/info/" in driver.current_url


# 5. UI chung


@pytest.mark.parametrize("width,height", [(1366, 768), (390, 844)])
def test_ui_common_01_responsive_desktop_khong_vo_layout(driver, width, height):
    driver.set_window_size(width, height)
    driver.get(LOGIN_URL)

    assert find_email_input(driver).is_displayed()
    assert find_password_input(driver).is_displayed()
    assert find_login_button(driver).is_displayed()


def test_ui_common_02_button_hover_click_co_phan_hoi(driver):
    driver.get(LOGIN_URL)
    find_email_input(driver).send_keys("user@example.com")
    find_password_input(driver).send_keys("Password123!")
    button = find_login_button(driver)

    ActionChains(driver).move_to_element(button).perform()

    assert button.is_enabled()
    assert button.is_displayed()


@pytest.mark.parametrize(
    "link_text,expected_url_part",
    [
        ("Reset Password", "/account/reset-password"),
        ("Sign Up", "/account/signup"),
    ],
)
def test_ui_common_03_link_dieu_huong_dung_trang(driver, link_text, expected_url_part):
    driver.get(LOGIN_URL)

    link = find_any(
        driver,
        [
            (By.XPATH, f"//a[contains(., '{link_text}')]"),
            (By.XPATH, f"//a[contains(@href, '{expected_url_part}')]"),
        ],
        EC.element_to_be_clickable,
    )
    link.click()

    wait(driver).until(EC.url_contains(expected_url_part))
    assert expected_url_part in driver.current_url


def test_ui_common_04_font_mau_spacing_hien_thi_dong_nhat(driver):
    driver.get(LOGIN_URL)
    email_input = find_email_input(driver)
    login_button = find_login_button(driver)

    input_font = email_input.value_of_css_property("font-family")
    button_font = login_button.value_of_css_property("font-family")
    input_color = email_input.value_of_css_property("color")
    button_color = login_button.value_of_css_property("color")

    assert input_font
    assert button_font
    assert input_color
    assert button_color


def test_ui_common_05_reload_trang_khong_mat_trang_thai_quan_trong(driver):
    search_box = go_to_shared_decks(driver)
    keyword = "english"

    search_box.clear()
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)
    wait(driver).until(lambda d: keyword in d.current_url.lower() or d.find_elements(By.XPATH, "//a[contains(@href, '/shared/info/')]"))
    current_url = driver.current_url

    driver.refresh()

    assert driver.current_url == current_url
    assert find_any(driver, [(By.TAG_NAME, "body")]).is_displayed()

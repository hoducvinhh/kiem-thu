import os
import time
from dataclasses import dataclass
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener

import pytest


BASE_URL = "https://ankiweb.net"
LOGIN_URL = f"{BASE_URL}/account/login"
SIGNUP_URL = f"{BASE_URL}/account/signup"
SHARED_LIST_DECKS_URL = f"{BASE_URL}/svc/shared/list-decks"
API_LOGIN_URL = f"{BASE_URL}/svc/account/login"
API_SIGNUP_URL = f"{BASE_URL}/svc/account/signup"
API_CREATE_DECK_URL = f"{BASE_URL}/svc/decks/create-deck"
DEFAULT_TIMEOUT = int(os.getenv("API_TIMEOUT_SECONDS", "10"))


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
ANKIWEB_COOKIE = os.getenv("ANKIWEB_COOKIE")


def auth_cookie_header(cookie_value):
    if "ankiweb=" in cookie_value:
        return cookie_value
    return f"has_auth=1; ankiweb={cookie_value}"


def encode_varint(value):
    output = bytearray()
    while value > 0x7F:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def encode_string_field(field_number, value):
    raw_value = value.encode("utf-8")
    return encode_varint((field_number << 3) | 2) + encode_varint(len(raw_value)) + raw_value


def encode_string_message(**fields):
    output = bytearray()
    for field_number, value in fields.items():
        if value is not None:
            output.extend(encode_string_field(int(field_number), value))
    return bytes(output)


def decode_varint(data, offset=0):
    shift = 0
    value = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ValueError("Incomplete protobuf varint")


def decode_scalar_fields(data):
    fields = {}
    offset = 0
    while offset < len(data):
        key, offset = decode_varint(data, offset)
        field_number = key >> 3
        wire_type = key & 0x07
        if wire_type == 0:
            value, offset = decode_varint(data, offset)
            fields.setdefault(field_number, []).append(value)
        elif wire_type == 2:
            length, offset = decode_varint(data, offset)
            value = data[offset : offset + length]
            offset += length
            fields.setdefault(field_number, []).append(value)
        else:
            raise ValueError(f"Unsupported protobuf wire type: {wire_type}")
    return fields


def decode_text(value):
    return value.decode("utf-8", errors="ignore")


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class ApiResponse:
    status_code: int
    url: str
    headers: object
    content: bytes

    @property
    def text(self):
        content_type = self.headers.get("content-type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=", 1)[1].split(";", 1)[0].strip()
        return self.content.decode(charset, errors="ignore")


class ApiSession:
    def __init__(self):
        self.cookies = CookieJar()
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
            "Referer": BASE_URL,
            "User-Agent": "Mozilla/5.0",
        }

    def get(self, url, params=None, headers=None, timeout=DEFAULT_TIMEOUT):
        return self.request("GET", url, params=params, headers=headers, timeout=timeout)

    def post(self, url, data=None, headers=None, allow_redirects=True, timeout=DEFAULT_TIMEOUT):
        return self.request(
            "POST",
            url,
            data=data,
            headers=headers,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def post_binary(self, url, body=b"", headers=None, allow_redirects=True, timeout=DEFAULT_TIMEOUT):
        return self.request(
            "POST",
            url,
            body=body,
            headers={"Content-Type": "application/octet-stream", **(headers or {})},
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        body=None,
        headers=None,
        allow_redirects=True,
        timeout=DEFAULT_TIMEOUT,
    ):
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(params)}"

        request_headers = {**self.headers, **(headers or {})}
        if data is not None:
            body = urlencode(data).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

        request = Request(url, data=body, headers=request_headers, method=method)
        handlers = [HTTPCookieProcessor(self.cookies)]
        if not allow_redirects:
            handlers.append(NoRedirectHandler())
        opener = build_opener(*handlers)

        try:
            response = opener.open(request, timeout=timeout)
            content = response.read()
            return ApiResponse(response.status, response.url, response.headers, content)
        except Exception as error:
            if hasattr(error, "code") and hasattr(error, "headers"):
                content = error.read() if hasattr(error, "read") else b""
                return ApiResponse(error.code, error.url, error.headers, content)
            raise

    def set_cookie_header(self, cookie_header):
        self.headers["Cookie"] = cookie_header

    def has_cookie(self, cookie_name):
        return any(cookie.name == cookie_name for cookie in self.cookies)


@pytest.fixture
def api_session():
    return ApiSession()


@pytest.fixture
def authenticated_api_session(api_session):
    if ANKIWEB_COOKIE:
        api_session.set_cookie_header(auth_cookie_header(ANKIWEB_COOKIE))
        return api_session

    if not ANKI_EMAIL or not ANKI_PASSWORD:
        pytest.skip("Set ANKIWEB_COOKIE or ANKI_EMAIL and ANKI_PASSWORD to run authenticated API tests.")

    response = api_session.post_binary(
        API_LOGIN_URL,
        body=encode_string_message(**{"1": ANKI_EMAIL, "2": ANKI_PASSWORD}),
        timeout=DEFAULT_TIMEOUT,
    )
    fields = decode_scalar_fields(response.content)
    status = fields.get(1, [0])[0]
    if status != 1:
        pytest.fail(f"API login failed with status {status}.")

    token_values = fields.get(2, [])
    if not token_values:
        pytest.fail("API login did not return an ankiuser token.")

    api_session.get(
        f"{BASE_URL}/account/ankiuser-login",
        params={"t": decode_text(token_values[0])},
        timeout=DEFAULT_TIMEOUT,
    )
    return api_session


def assert_not_server_error(response):
    assert response.status_code < 500


# 1. Dang nhap


def test_api_login_01_get_form_dang_nhap_tra_200(api_session):
    response = api_session.get(LOGIN_URL, timeout=DEFAULT_TIMEOUT)

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<html" in response.text.lower()


def test_api_login_02_sai_email_password_khong_dang_nhap(api_session):
    response = api_session.post_binary(
        API_LOGIN_URL,
        body=encode_string_message(**{"1": "wrong-user@example.com", "2": "SaiMatKhauHoanToan123"}),
        timeout=DEFAULT_TIMEOUT,
    )
    fields = decode_scalar_fields(response.content)

    assert response.status_code == 200
    assert_not_server_error(response)
    assert not api_session.has_cookie("ankiweb")
    assert fields.get(1, [0])[0] in (2, 3)


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "", "password": "Password123!"},
        {"email": "user@example.com", "password": ""},
        {"email": "email_sai_dinh_dang", "password": "Password123!"},
    ],
)
def test_api_login_03_du_lieu_khong_hop_le_khong_loi_server(api_session, payload):
    response = api_session.post_binary(
        API_LOGIN_URL,
        body=encode_string_message(**{"1": payload["email"], "2": payload["password"]}),
        timeout=DEFAULT_TIMEOUT,
    )
    fields = decode_scalar_fields(response.content)

    assert response.status_code == 200
    assert_not_server_error(response)
    assert not api_session.has_cookie("ankiweb")
    assert fields.get(1, [0])[0] in (0, 2, 3)


# 2. Dang ky


def test_api_register_01_get_form_dang_ky_tra_200(api_session):
    response = api_session.get(SIGNUP_URL, timeout=DEFAULT_TIMEOUT)

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<html" in response.text.lower()


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "", "password": "Password123!"},
        {"email": "email_sai_dinh_dang", "password": "Password123!"},
        {"email": "email_sai_dinh_dang", "password": ""},
        {"email": "user name@example.com", "password": "Password123!"},
    ],
)
def test_api_register_02_du_lieu_khong_hop_le_khong_tao_tai_khoan(api_session, payload):
    response = api_session.post_binary(
        API_SIGNUP_URL,
        body=encode_string_message(**{"1": payload["email"], "2": payload["password"]}),
        timeout=DEFAULT_TIMEOUT,
    )
    fields = decode_scalar_fields(response.content)

    assert response.status_code == 200
    assert_not_server_error(response)
    assert fields.get(1, [0])[0] in (0, 2, 3, 4)


# 3. Tim kiem


def assert_shared_decks_api_response(response):
    if "text/html" in response.headers.get("content-type", ""):
        pytest.fail("AnkiWeb returned HTML instead of the shared-decks API payload.")


def test_api_search_01_tu_khoa_hop_le_tra_du_lieu(authenticated_api_session):
    response = authenticated_api_session.get(
        SHARED_LIST_DECKS_URL,
        params={"search": "english"},
        headers={"Referer": f"{BASE_URL}/shared/decks"},
        timeout=DEFAULT_TIMEOUT,
    )

    assert_shared_decks_api_response(response)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/octet-stream"
    assert len(response.content) > 1000


def test_api_search_02_tu_khoa_rong_tra_200(authenticated_api_session):
    response = authenticated_api_session.get(
        SHARED_LIST_DECKS_URL,
        params={"search": ""},
        headers={"Referer": f"{BASE_URL}/shared/decks"},
        timeout=DEFAULT_TIMEOUT,
    )

    assert_shared_decks_api_response(response)
    assert response.status_code == 200
    assert len(response.content) < 1000


@pytest.mark.parametrize("keyword", ["zzzzzzzzzz_no_deck_should_match_2026", "@#$%^&*()[]{}", "a" * 300])
def test_api_search_03_input_bien_khong_loi_server(authenticated_api_session, keyword):
    response = authenticated_api_session.get(
        SHARED_LIST_DECKS_URL,
        params={"search": keyword},
        headers={"Referer": f"{BASE_URL}/shared/decks"},
        timeout=DEFAULT_TIMEOUT,
    )

    assert_shared_decks_api_response(response)
    assert response.status_code == 200
    assert_not_server_error(response)


def test_api_search_04_co_header_cache(authenticated_api_session):
    response = authenticated_api_session.get(
        SHARED_LIST_DECKS_URL,
        params={"search": "english"},
        headers={"Referer": f"{BASE_URL}/shared/decks"},
        timeout=DEFAULT_TIMEOUT,
    )

    assert_shared_decks_api_response(response)
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "max-age=600"


# 4. Tao moi deck


def test_api_create_01_chua_dang_nhap_khong_duoc_tao_deck(api_session):
    response = api_session.post_binary(
        API_CREATE_DECK_URL,
        body=encode_string_message(**{"1": f"Api_Unauth_Test_{int(time.time())}"}),
        allow_redirects=False,
        timeout=DEFAULT_TIMEOUT,
    )

    assert response.status_code in (401, 403)


def test_api_create_02_ten_rong_bi_tu_choi(authenticated_api_session):
    response = authenticated_api_session.post_binary(
        API_CREATE_DECK_URL,
        body=encode_string_message(**{"1": ""}),
        timeout=DEFAULT_TIMEOUT,
    )

    assert response.status_code in (200, 400, 422)
    assert_not_server_error(response)


def test_api_create_03_ten_qua_dai_bi_tu_choi_hoac_khong_loi_server(authenticated_api_session):
    response = authenticated_api_session.post_binary(
        API_CREATE_DECK_URL,
        body=encode_string_message(**{"1": "A" * 300}),
        timeout=DEFAULT_TIMEOUT,
    )

    assert response.status_code in (200, 400, 422)
    assert_not_server_error(response)

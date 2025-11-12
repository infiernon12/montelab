import requests
import json
import time
import hmac
import hashlib
import random
import string
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import ssl
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LicenseClient:
    def __init__(self, api_base_url: str, hmac_secret_key: str, hwid: str):
        self.api_base_url = "https://185.221.196.69:8000/api/v1/"
        self.hmac_secret_key = hmac_secret_key  
        self.hwid = hwid
        self.last_check = None
        self.expected_cert_fingerprint = None
        self.ssl_verification_enabled = True
        
    def _generate_hmac_signature(self, data: str) -> str:
        """Генерация HMAC-SHA256 подписи для данных"""
        # КРИТИЧНО: используем тот же ключ что на сервере
        secret_key = "28de6a1eb3b9e9edb29c886a43d71964935bd12cb981cc2e604381076d73f6660fdca0a6092ee4b055882859563e7c373472d01d28d0e91cefa810bc1106c572"
        return hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _generate_nonce(self, length=8) -> str:
        """Генерация случайного nonce"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _make_request(self, endpoint: str, data: Dict[Any, Any]) -> Optional[Dict[Any, Any]]:
        """
        HMAC запрос с SSL Pinning проверкой
        
        Returns:
            Dict - успешный ответ от сервера
            None - ошибка связи, таймаут или НЕВЕРНАЯ ПОДПИСЬ запроса
        """
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            # SSL Pinning проверка перед запросом
            if not self.verify_ssl_certificate(url):
                logger.error("SSL Pinning verification failed - aborting request")
                return None
                
            json_data = json.dumps(data)
            signature = self._generate_hmac_signature(json_data)
            
            headers = {
                "Content-Type": "application/json",
                "X-Signature": signature
            }
            
            logger.info(f"Making request to {endpoint}")
            logger.debug(f"Request signature: {signature[:16]}...")
            
            response = requests.post(url, data=json_data, headers=headers, timeout=10, verify=False)
            
            # ИСПРАВЛЕНИЕ: различаем типы ошибок
            if response.status_code == 200:
                # Успешный ответ
                logger.info("Server returned 200 OK")
                return response.json()
                
            elif response.status_code == 401:
                # 401 = НЕВЕРНАЯ HMAC ПОДПИСЬ ЗАПРОСА
                logger.error("❌ HMAC SIGNATURE VERIFICATION FAILED ON SERVER")
                logger.error("This means the request signature is invalid!")
                logger.error(f"Response: {response.text}")
                return None  # ⚠️ Возвращаем None, НЕ словарь!
                
            elif response.status_code == 404:
                # 404 = Лицензия не найдена в БД (валидная подпись, но нет HWID)
                logger.warning(f"License not found for HWID: {self.hwid}")
                # Возвращаем структурированный ответ
                return {
                    "is_active": False,
                    "error": "license_not_found",
                    "message": "No license found for this HWID"
                }
                
            elif response.status_code == 400:
                # 400 = Некорректный формат запроса
                logger.error(f"Bad request: {response.text}")
                return None
                
            elif response.status_code == 403:
                # 403 = Лицензия найдена, но неактивна/истекла
                logger.warning("License found but inactive or expired")
                return response.json()  # Сервер вернет {"is_active": false, ...}
                
            else:
                logger.error(f"Unexpected status code: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during license check: {e}")
            return None
    
    def check_license(self) -> bool:
        """
        Проверка лицензии согласно ТЗ
        
        Returns:
            True - валидная активная лицензия
            False - невалидная/неактивная лицензия или ошибка
        """
        request_data = {
            "hwid": self.hwid,
            "timestamp": int(time.time()),
            "nonce": self._generate_nonce()
        }
        
        logger.info("=" * 60)
        logger.info("CHECKING LICENSE")
        logger.info(f"HWID: {self.hwid}")
        logger.info("=" * 60)
        
        result = self._make_request("license/check", request_data)
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: None означает ошибку HMAC или связи
        if result is None:
            logger.error("❌ LICENSE CHECK FAILED")
            logger.error("Reason: Invalid HMAC signature or connection error")
            logger.error("The server rejected the request or is unreachable")
            return False
        
        # Сервер ответил успешно - проверяем подпись ответа
        self.last_check = datetime.now()
        
        # Проверка подписи ответа от сервера
        if 'signature' not in result:
            logger.warning("⚠️ Server response missing signature field")
            # Если нет подписи, но есть error - это 404 (лицензия не найдена)
            if 'error' in result:
                logger.info(f"Error type: {result.get('error')}")
                return False
            # Подозрительно - нет ни подписи, ни error
            logger.error("❌ Suspicious response format")
            return False
        
        response_copy = result.copy()
        received_signature = response_copy.pop('signature', '')
        response_json = json.dumps(response_copy, sort_keys=True)
        expected_signature = self._generate_hmac_signature(response_json)
        
        logger.debug(f"Received signature: {received_signature[:16]}...")
        logger.debug(f"Expected signature: {expected_signature[:16]}...")
        
        if received_signature != expected_signature:
            logger.error("❌ INVALID RESPONSE SIGNATURE FROM SERVER")
            logger.error("The server's response signature does not match!")
            logger.error("Possible MITM attack or server compromise!")
            return False
        
        logger.info("✅ Response signature verified")
        
        # Проверяем статус лицензии
        is_active = result.get('is_active', False)
        
        if is_active:
            logger.info("=" * 60)
            logger.info("✅ LICENSE VALID AND ACTIVE")
            logger.info("=" * 60)
        else:
            logger.warning("=" * 60)
            logger.warning("❌ LICENSE INACTIVE OR EXPIRED")
            logger.warning("=" * 60)
        
        return is_active
    
    def get_license_info(self) -> Optional[Dict[Any, Any]]:
        """Получение детальной информации о лицензии"""
        request_data = {
            "hwid": self.hwid,
            "timestamp": int(time.time()),
            "nonce": self._generate_nonce()
        }
        
        return self._make_request("license/info", request_data)
    
    def get_certificate_fingerprint(self, hostname: str, port: int = 443) -> Optional[str]:
        """Получить SHA-256 отпечаток SSL сертификата сервера"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(True)
                    fingerprint = hashlib.sha256(cert_der).hexdigest()
                    logger.info(f"Certificate fingerprint: {fingerprint}")
                    return fingerprint
        except Exception as e:
            logger.error(f"Failed to get certificate fingerprint: {e}")
            return None

    def verify_ssl_certificate(self, url: str) -> bool:
        """Проверить SSL сертификат согласно SSL pinning"""
        if not self.ssl_verification_enabled:
            return True
            
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        current_fingerprint = self.get_certificate_fingerprint(hostname, port)
        if not current_fingerprint:
            logger.error("Could not retrieve certificate fingerprint")
            return False
        
        if not self.expected_cert_fingerprint:
            # При первом подключении сохранить отпечаток
            self.expected_cert_fingerprint = current_fingerprint
            logger.info("SSL pinning: Saved certificate fingerprint for future verification")
            return True
        
        if current_fingerprint != self.expected_cert_fingerprint:
            logger.error("SSL PINNING VIOLATION: Certificate fingerprint mismatch!")
            logger.error(f"Expected: {self.expected_cert_fingerprint}")
            logger.error(f"Received: {current_fingerprint}")
            return False
        
        logger.info("SSL pinning: Certificate verified successfully")
        return True
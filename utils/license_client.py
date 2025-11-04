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
import urllib3
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LicenseClient:
    def __init__(self, api_base_url: str, hmac_secret_key: str, hwid: str):
        self.api_base_url = "https://85.239.147.227/api/v1/"
        self.hmac_secret_key = hmac_secret_key  
        self.hwid = hwid
        self.last_check = None
        self.expected_cert_fingerprint = None  # Будет установлен при первом подключении
        self.ssl_verification_enabled = True
        
    def _generate_hmac_signature(self, data: str) -> str:
        """Генерация HMAC-SHA256 подписи для данных"""
        import hmac
        secret_key = "super-secure-hmac-key-for-production-change-this-immediately"  # Тот же ключ что на сервере
        return hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    
    def _generate_nonce(self, length=8) -> str:
        """Генерация случайного nonce"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _make_request(self, endpoint: str, data: Dict[Any, Any]) -> Optional[Dict[Any, Any]]:
        """HMAC запрос с SSL Pinning проверкой"""
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
            
            response = requests.post(url, data=json_data, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code in [400, 401, 404]:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return {"is_active": False}
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
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
        """Проверка лицензии согласно ТЗ"""
        request_data = {
            "hwid": self.hwid,
            "timestamp": int(time.time()),
            "nonce": self._generate_nonce()
        }
        
        result = self._make_request("license/check", request_data)
        
        if result is not None:
            # Сервер ответил (успешно или с ошибкой лицензии)
            self.last_check = datetime.now()
            
            # Проверяем подпись ответа для дополнительной безопасности
            response_copy = result.copy()
            signature = response_copy.pop('signature', '')
            response_json = json.dumps(response_copy, sort_keys=True)
            expected_signature = self._generate_hmac_signature(response_json)
            
            if signature != expected_signature:
                logger.error("Invalid response signature from server")
                return False
            
            # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: возвращаем точный статус из БД
            is_active = result.get('is_active', False)
            logger.info(f"Server responded: is_active={is_active}")
            return is_active
            
        else:
            # ТОЛЬКО здесь включаем Grace Period - когда сервер НЕДОСТУПЕН
            logger.error("License check failed - no server response")
            return False 

    
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


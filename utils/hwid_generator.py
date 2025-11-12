import hashlib
import platform
import subprocess
import uuid
import re
from typing import Optional

class HWIDGenerator:
    """Генератор устойчивого HWID на основе характеристик оборудования"""
    
    @staticmethod
    def get_system_disk_serial() -> str:
        """Получение серийного номера системного диска"""
        try:
            if platform.system() == 'Windows':
                # Windows - через WMI
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                      capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Пропускаем заголовок
                    serial = line.strip()
                    if serial and serial != 'SerialNumber':
                        return serial
            else:
                # Linux/Mac - через lsblk или diskutil
                result = subprocess.run(['lsblk', '-o', 'SERIAL', '-n'], 
                                      capture_output=True, text=True)
                if result.stdout:
                    serials = [s.strip() for s in result.stdout.split('\n') if s.strip()]
                    if serials:
                        return serials[0]
        except Exception:
            pass
        return "UNKNOWN_DISK_SERIAL"
    
    @staticmethod
    def get_cpu_id() -> str:
        """Получение ID процессора"""
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['wmic', 'cpu', 'get', 'processorid'], 
                                      capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    cpu_id = line.strip()
                    if cpu_id and cpu_id != 'ProcessorId':
                        return cpu_id
            else:
                # Linux - через /proc/cpuinfo
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'processor' in line.lower():
                            return line.split(':')[1].strip()
        except Exception:
            pass
        return "UNKNOWN_CPU_ID"
    
    @staticmethod
    def get_primary_mac() -> str:
        """Получение MAC-адреса основного сетевого интерфейса"""
        try:
            # Получаем MAC-адрес через uuid
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            return mac
        except Exception:
            return "UNKNOWN_MAC_ADDRESS"
    
    @staticmethod
    def get_motherboard_serial() -> str:
        """Получение серийного номера материнской платы"""
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                      capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    serial = line.strip()
                    if serial and serial != 'SerialNumber':
                        return serial
            else:
                # Linux - через dmidecode
                result = subprocess.run(['dmidecode', '-s', 'baseboard-serial-number'], 
                                      capture_output=True, text=True)
                if result.stdout:
                    return result.stdout.strip()
        except Exception:
            pass
        return "UNKNOWN_MOTHERBOARD"
    
    @staticmethod
    def get_bios_serial() -> str:
        """Получение серийного номера BIOS"""
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['wmic', 'bios', 'get', 'serialnumber'], 
                                      capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    serial = line.strip()
                    if serial and serial != 'SerialNumber':
                        return serial
            else:
                result = subprocess.run(['dmidecode', '-s', 'bios-serial-number'], 
                                      capture_output=True, text=True)
                if result.stdout:
                    return result.stdout.strip()
        except Exception:
            pass
        return "UNKNOWN_BIOS"
    
    @classmethod
    def generate_hwid(cls) -> str:
        """Генерация устойчивого HWID"""
        # Собираем все идентификаторы
        components = [
            cls.get_system_disk_serial(),
            cls.get_cpu_id(),
            cls.get_primary_mac(),
            cls.get_motherboard_serial(),
            cls.get_bios_serial(),
            platform.machine(),
            platform.system(),
            "qpkeo2k2ok2kmdk123PENISd2"
        ]
        
        # Объединяем и хешируем
        combined_string = "|".join(components)
        hwid_hash = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
        
        # Форматируем в виде групп по 8 символов
        formatted_hwid = '-'.join([hwid_hash[i:i+8].upper() for i in range(0, 32, 8)])
        
        return formatted_hwid

import logging
from datetime import datetime
from typing import Dict, Any, Tuple

# Настройка логирования
logger = logging.getLogger(__name__)

# Пытаемся импортировать PyEphem, обрабатываем ошибки если недоступен
EPHEM_AVAILABLE = False
try:
    import ephem
    EPHEM_AVAILABLE = True
except ImportError:
    logger.warning("Библиотека PyEphem не установлена. Натальная карта будет создана с заполнителями.")

# Словарь с координатами некоторых городов (широта, долгота)
CITY_COORDINATES = {
    "Москва": (55.7558, 37.6173),
    "Санкт-Петербург": (59.9343, 30.3351),
    # Можно добавить другие города по мере необходимости
}

def get_coordinates(city: str) -> Tuple[float, float]:
    """
    Получение координат города.
    
    Args:
        city: Название города.
        
    Returns:
        Tuple[float, float]: Координаты (широта, долгота).
    """
    # Для MVP возвращаем координаты из словаря или (0, 0) если город не найден
    return CITY_COORDINATES.get(city, (0.0, 0.0))

def make_natal_chart(date_str: str, city: str, name: str = None) -> Dict[str, Any]:
    """
    Создание натальной карты на основе даты и места рождения.
    
    Args:
        date_str: Дата и время рождения в формате "YYYY-MM-DD HH:MM".
        city: Название города рождения.
        name: Имя человека (опционально).
        
    Returns:
        Dict[str, Any]: JSON-объект с данными натальной карты.
    """
    # Проверяем, доступен ли PyEphem
    if not EPHEM_AVAILABLE:
        logger.warning("Создание натальной карты невозможно: PyEphem не установлен")
        return {
            "note": "Натальная карта создана с заполнителями (PyEphem не установлен)",
            "sun_long": 0.0,
            "moon_long": 0.0,
            "mercury_long": 0.0,
            "venus_long": 0.0,
            "mars_long": 0.0,
            "jupiter_long": 0.0,
            "saturn_long": 0.0,
            "coordinates": {
                "latitude": 0.0,
                "longitude": 0.0
            },
            "date": date_str,
            "city": city,
            "name": name
        }
    
    try:
        # Получаем координаты города
        lat, lon = get_coordinates(city)
        
        # Настраиваем наблюдателя (Observer)
        observer = ephem.Observer()
        observer.lat = str(lat)  # Широта в радианах или в строковом формате "55:45:00.0"
        observer.lon = str(lon)  # Долгота в радианах или в строковом формате "37:37:00.0"
        
        # Преобразуем строку даты в объект даты для ephem
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            observer.date = dt.strftime("%Y/%m/%d %H:%M:%S")
        except ValueError:
            logger.error(f"Неверный формат даты: {date_str}. Используется текущая дата.")
            # Возвращаем ошибку вместо использования текущей даты
            return {
                "error": f"Неверный формат даты: {date_str}",
                "date": date_str,
                "city": city,
                "name": name
            }
        
        # Рассчитываем положения небесных тел
        sun = ephem.Sun(observer)
        moon = ephem.Moon(observer)
        mercury = ephem.Mercury(observer)
        venus = ephem.Venus(observer)
        mars = ephem.Mars(observer)
        jupiter = ephem.Jupiter(observer)
        saturn = ephem.Saturn(observer)
        
        # Расчет асцендента (приблизительно)
        # Для точного расчета асцендента требуется более сложный алгоритм
        
        # Создаем результирующий JSON-объект
        result = {
            "sun_long": float(sun.hlong),
            "moon_long": float(moon.hlong),
            "mercury_long": float(mercury.hlong),
            "venus_long": float(venus.hlong),
            "mars_long": float(mars.hlong),
            "jupiter_long": float(jupiter.hlong),
            "saturn_long": float(saturn.hlong),
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "date": date_str,
            "name": name
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Ошибка при создании натальной карты: {e}")
        # Возвращаем минимальный набор данных в случае ошибки
        return {
            "error": str(e),
            "date": date_str,
            "city": city,
            "name": name
        } 
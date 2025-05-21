import pytest
from datetime import datetime
from services.astrology import make_natal_chart, get_coordinates

def test_get_coordinates():
    """Тест для функции get_coordinates."""
    # Тест для известного города
    lat, lon = get_coordinates("Москва")
    assert lat == 55.7558
    assert lon == 37.6173
    
    # Тест для неизвестного города
    lat, lon = get_coordinates("НесуществующийГород")
    assert lat == 0.0
    assert lon == 0.0

def test_make_natal_chart():
    """Тест для функции make_natal_chart."""
    # Тест с корректными данными
    date_str = "2000-01-01 12:00"
    city = "Москва"
    
    result = make_natal_chart(date_str, city)
    
    # Проверяем наличие необходимых ключей в результате
    assert "sun_long" in result
    assert "moon_long" in result
    assert "coordinates" in result
    assert "date" in result
    
    # Проверяем значения координат
    assert result["coordinates"]["latitude"] == 55.7558
    assert result["coordinates"]["longitude"] == 37.6173
    
    # Проверяем формат даты
    assert result["date"] == date_str
    
    # Тест с некорректным форматом даты
    result_invalid_date = make_natal_chart("invalid-date", city)
    assert "error" in result_invalid_date 
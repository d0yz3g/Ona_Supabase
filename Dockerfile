FROM python:3.11-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt railway_requirements.txt ./
COPY supabase_requirements.txt ./

# Устанавливаем базовые зависимости
RUN pip install --no-cache-dir -r railway_requirements.txt

# Копируем скрипты и делаем их исполняемыми
COPY start.sh install_supabase.sh ./
RUN chmod +x start.sh install_supabase.sh

# Копируем оставшиеся файлы проекта
COPY . .

# Установка совместимой версии pydantic
RUN pip install --no-cache-dir pydantic==1.10.12

# Создаем необходимые директории
RUN mkdir -p logs tmp

# Запускаем бота
CMD ["bash", "start.sh"] 
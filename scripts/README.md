# Telegram Channel Posts Scraper

Этот репозиторий автоматически собирает последние 20 постов из Telegram канала [@ordendog](https://t.me/ordendog) и сохраняет их в формате JSON для интеграции с сайтом.

## Как это работает

1. GitHub Actions запускает скрипт каждые 6 часов
2. Скрипт парсит публичную страницу канала @ordendog
3. Извлекаются текст, дата, ссылка и медиа (если есть)
4. Данные сохраняются в `data/posts.json`
5. Изменения автоматически коммитятся в репозиторий

## Использование на сайте

Вы можете использовать JSON файл напрямую с GitHub:

```javascript
fetch('https://raw.githubusercontent.com/ваш-username/telegram-ordendog-scraper/main/data/posts.json')
  .then(response => response.json())
  .then(data => {
    // Обработка данных
    console.log(data.posts);
  });

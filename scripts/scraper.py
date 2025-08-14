import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

CHANNEL_URL = "https://t.me/s/ordendog"
OUTPUT_FILE = "../data/posts.json"
MAX_POSTS = 20

def scrape_telegram_channel():
    try:
        # Создаем папку data, если её нет
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        # Получаем HTML страницы
        response = requests.get(CHANNEL_URL)
        response.raise_for_status()
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все посты
        post_elements = soup.find_all('div', class_='tgme_widget_message_wrap')
        posts = []
        
        for post in post_elements[:MAX_POSTS]:
            try:
                # Извлекаем данные
                message = post.find('div', class_='tgme_widget_message_text')
                if not message:
                    continue
                    
                text = message.get_text('\n').strip()
                date_element = post.find('time', class_='time')
                date = date_element['datetime'] if date_element else str(datetime.now())
                link = post.find('a', class_='tgme_widget_message_date')['href']
                
                # Может быть медиа (фото/видео)
                media = post.find('a', class_='tgme_widget_message_photo_wrap')
                media_url = media['style'].split("url('")[1].split("')")[0] if media else None
                
                posts.append({
                    'text': text,
                    'date': date,
                    'link': link,
                    'media_url': media_url
                })
            except Exception as e:
                print(f"Error parsing post: {e}")
                continue
        
        # Сортируем посты по дате (новые сверху)
        posts.sort(key=lambda x: x['date'], reverse=True)
        
        # Сохраняем в JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'last_updated': str(datetime.now()),
                'posts': posts
            }, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully scraped {len(posts)} posts")
        
    except Exception as e:
        print(f"Error scraping channel: {e}")

if __name__ == "__main__":
    scrape_telegram_channel()

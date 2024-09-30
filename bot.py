import requests
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN, USERNAME, PASSWORD

# Initialize the Pyrogram bot
app = Client("crunchyroll_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Crunchyroll login URL and headers
login_url = "https://www.crunchyroll.com/login"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# Function to log in to Crunchyroll and maintain a session
def login_crunchyroll(session):
    try:
        login_page = session.get(login_url, headers=headers)
        soup = BeautifulSoup(login_page.content, 'html.parser')

        # Find the CSRF token (if needed)
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

        # Login data with credentials from config
        login_data = {
            'login_form[email]': USERNAME,
            'login_form[password]': PASSWORD,
            'csrfmiddlewaretoken': csrf_token
        }

        login_response = session.post(login_url, data=login_data, headers=headers)
        if "My Account" in login_response.text:
            return True
        return False
    except Exception as e:
        print(f"Login failed: {e}")
        return False

# Function to scrape premium episodes
def get_latest_premium_episodes(session, url):
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        episodes = []
        for episode in soup.find_all('li', class_='episode'):
            title = episode.find('a', class_='episode-title').text.strip()
            link = "https://www.crunchyroll.com" + episode.find('a', class_='episode-title')['href']
            pub_date = episode.find('span', class_='release-date').text.strip()

            episodes.append({
                'title': title,
                'link': link,
                'pub_date': pub_date
            })
        return episodes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching episodes: {e}")
        return None

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello! I’m a Crunchyroll RSS feed bot. Use /get_latest_premium_episodes to get the latest premium episodes.")

# Command handler for getting the latest premium episodes
@app.on_message(filters.command("get_latest_premium_episodes"))
async def send_latest_premium_episodes(client, message):
    url = "https://www.crunchyroll.com/series-episodes"  # Replace with the actual premium series URL
    
    status_message = await message.reply_text("Attempting to log in to Crunchyroll...")

    with requests.Session() as session:
        if login_crunchyroll(session):
            await status_message.edit_text("Login successful! Fetching the latest premium episodes...")

            episodes = get_latest_premium_episodes(session, url)
            if episodes:
                reply_text = "Here are the latest premium episodes:\n\n"
                for ep in episodes:
                    reply_text += f"Title: {ep['title']}\nLink: {ep['link']}\nDate: {ep['pub_date']}\n\n"
                await status_message.edit_text(reply_text)
            else:
                await status_message.edit_text("Failed to retrieve the episodes. Please try again later.")
        else:
            await status_message.edit_text("Login to Crunchyroll failed. Please check your credentials and try again.")

# Run the bot
app.run()

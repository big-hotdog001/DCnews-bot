# Discord News Bot

This is a simple Discord bot that provides the latest news headlines, allows searching for specific topics, and can summarize articles for you.

## Features

- **Top Headlines:** Get the latest top news headlines.
- **Categorized News:** Filter news by categories like business, technology, sports, etc.
- **Search:** Search for news on any topic.
- **Trending Topics:** See what's currently trending in the news.
- **Summaries:** Get AI-powered summaries of news articles.
- **Interactive Browsing:** Use buttons to navigate through news articles.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A Discord account and a Discord server where you have permission to add bots.
- API keys for:
    - [NewsAPI](https://newsapi.org/)
    - [Groq](https://console.groq.com/keys)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/news-bot.git
   cd news-bot
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create a `.env` file:**
   Create a file named `.env` in the project root and add your API keys:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   NEWS_API_KEY=your_news_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## How to Use

Once the bot is running and added to your Discord server, you can use the following commands:

- `!help`: Shows a list of all available commands.
- `!news`: Fetches the top 5 news headlines.
- `!news <category>`: Fetches the top 5 news headlines for a specific category. Available categories are: `business`, `entertainment`, `general`, `health`, `science`, `sports`, `technology`.
- `!search <keyword>`: Searches for news articles related to the provided keyword.
- `!trending`: Shows the top 5 trending keywords in the news.

After using `!news` or `!search`, you can use the `◀️ Previous` and `Next ▶️` buttons to browse through more articles.
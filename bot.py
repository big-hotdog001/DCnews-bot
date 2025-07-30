
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from newsapi import NewsApiClient
from discord.ui import View, Button
import re
from collections import Counter
from groq import Groq


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

newsapi = NewsApiClient(api_key=NEWS_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# In-memory storage for user's news session
user_data = {}

class NewsPaginator(View):
    def __init__(self, ctx, articles):
        super().__init__(timeout=180) # 3 minute timeout
        self.ctx = ctx
        self.articles = articles
        self.current_page = 0

    async def show_page(self, interaction: discord.Interaction):
        start = self.current_page * 5
        end = start + 5
        page_articles = self.articles[start:end]

        # Update the embed with the new articles
        await interaction.response.edit_message(embeds=[create_article_embed(article) for article in page_articles], view=self)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        self.current_page -= 1
        self.next_button.disabled = False
        if self.current_page == 0:
            self.previous_button.disabled = True
        await self.show_page(interaction)

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.current_page += 1
        self.previous_button.disabled = False
        if (self.current_page + 1) * 5 >= len(self.articles):
            self.next_button.disabled = True
        await self.show_page(interaction)


bot.remove_command('help')

@bot.command()
async def help(ctx):
    """Shows this help message."""
    embed = discord.Embed(
        title="News Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.green()
    )
    embed.add_field(name="!news", value="Shows the top 5 news headlines.", inline=False)
    embed.add_field(name="!news <category>", value="Shows the top 5 news headlines for a specific category (e.g., business, technology).", inline=False)
    embed.add_field(name="!next", value="Shows the next 5 news headlines.", inline=False)
    embed.add_field(name="!search <keyword>", value="Searches for news articles based on a keyword.", inline=False)
    embed.add_field(name="!trending", value="Shows the top 5 trending keywords in the news.", inline=False)
    embed.add_field(name="!help", value="Shows this help message.", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def news(ctx, *, category: str = None):
    """Fetches and displays the top 5 news articles with a summary."""
    available_categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
    if category and category.lower() not in available_categories:
        await ctx.send(f"Invalid category. Please choose from the following: `{'`, `'.join(available_categories)}`")
        return

    if category:
        top_headlines = newsapi.get_top_headlines(category=category.lower(), language='en', country='us', page_size=30)
    else:
        top_headlines = newsapi.get_top_headlines(language='en', country='us', page_size=30)
    
    articles = top_headlines.get('articles', [])
    
    if not articles:
        await ctx.send("No news found.")
        return

    user_id = ctx.author.id
    user_data[user_id] = {
        'articles': articles,
        'index': 0
    }

    news_text = ""
    for article in articles[:5]:
        news_text += f"Title: {article['title']}\n"
        news_text += f"Description: {article['description']}\n"
        news_text += f"URL: {article['url']}\n\n"

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Summarize the following news articles:\n\n{news_text}",
            }
        ],
        model="llama3-8b-8192",
        max_tokens=1024,  # Limit the summary length
    )
    
    summary = chat_completion.choices[0].message.content
    
    # Split the summary into chunks of 2000 characters or less
    chunks = [summary[i:i + 2000] for i in range(0, len(summary), 2000)]
    
    await ctx.send("**Top News Headlines:**")
    for chunk in chunks:
        await ctx.send(chunk)

    await send_articles(ctx, articles[:5])
    user_data[user_id]['index'] = 5

@bot.command(name='next')
async def next_news(ctx):
    """Displays the next 5 news articles."""
    user_id = ctx.author.id
    if user_id not in user_data or not user_data[user_id]['articles']:
        await ctx.send("No news to display. Use the `!news` command first.")
        return

    user_session = user_data[user_id]
    articles = user_session['articles']
    index = user_session['index']

    if index >= len(articles):
        await ctx.send("No more news articles.")
        return

    next_articles = articles[index:index + 5]

    news_text = ""
    for article in next_articles:
        news_text += f"Title: {article['title']}\n"
        news_text += f"Description: {article['description']}\n"
        news_text += f"URL: {article['url']}\n\n"

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Summarize the following news articles:\n\n{news_text}",
            }
        ],
        model="llama3-8b-8192",
        max_tokens=1024,
    )
    
    summary = chat_completion.choices[0].message.content
    
    chunks = [summary[i:i + 2000] for i in range(0, len(summary), 2000)]
    
    await ctx.send("**Here are the next news headlines:**")
    for chunk in chunks:
        await ctx.send(chunk)

    await send_articles(ctx, next_articles)
    user_session['index'] += 5

@bot.command()
async def search(ctx, *, keyword: str):
    """Searches for news articles based on a keyword."""
    all_articles = newsapi.get_everything(q=keyword, language='en', sort_by='relevancy', page_size=30)
    articles = all_articles.get('articles', [])
    
    if not articles:
        await ctx.send(f"No news found for '{keyword}'.")
        return

    user_id = ctx.author.id
    user_data[user_id] = {
        'articles': articles,
        'index': 0
    }

    news_text = ""
    for article in articles[:5]:
        news_text += f"Title: {article['title']}\n"
        news_text += f"Description: {article['description']}\n"
        news_text += f"URL: {article['url']}\n\n"

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Summarize the following news articles about '{keyword}':\n\n{news_text}",
            }
        ],
        model="llama3-8b-8192",
        max_tokens=1024,
    )
    
    summary = chat_completion.choices[0].message.content
    
    chunks = [summary[i:i + 2000] for i in range(0, len(summary), 2000)]
    
    await ctx.send(f"**News about '{keyword}':**")
    for chunk in chunks:
        await ctx.send(chunk)

    await send_articles(ctx, articles[:5])
    user_data[user_id]['index'] = 5

@bot.command()
async def trending(ctx):
    """Shows the top 5 trending keywords in the news."""
    async with ctx.typing():
        top_headlines = newsapi.get_top_headlines(language='en', country='us', page_size=100)
        articles = top_headlines.get('articles', [])

        if not articles:
            await ctx.send("Could not fetch trending topics.")
            return

        # Extract words from titles
        all_words = []
        for article in articles:
            words = re.findall(r'\b\w+\b', article['title'].lower())
            all_words.extend(words)

        # Remove common English stop words
        stop_words = set(["the", "a", "an", "is", "are", "to", "in", "for", "of", "on", "and", "with", "as", "by", "at", "from", "-"])
        filtered_words = [word for word in all_words if word not in stop_words and not word.isdigit()]

        # Get the most common words
        word_counts = Counter(filtered_words)
        most_common_words = word_counts.most_common(5)

        embed = discord.Embed(
            title="🔥 Trending Topics",
            description="Here are the top 5 trending keywords in the news right now:",
            color=discord.Color.orange()
        )

        for i, (word, count) in enumerate(most_common_words, 1):
            embed.add_field(name=f"#{i} {word.capitalize()}", value=f"Mentioned {count} times", inline=False)

        await ctx.send(embed=embed)

def create_article_embed(article):
    embed = discord.Embed(
        title=article.get('title'),
        description=article.get('description'),
        url=article.get('url'),
        color=discord.Color.blue()
    )
    if article.get('urlToImage'):
        embed.set_image(url=article.get('urlToImage'))
    
    source_name = article.get('source', {}).get('name', 'Unknown Source')
    embed.set_footer(text=f"Source: {source_name}")
    return embed

async def send_articles(ctx, articles):
    """Sends a list of articles as embeds."""
    for article in articles:
        embed = discord.Embed(
            title=article.get('title'),
            description=article.get('description'),
            url=article.get('url'),
            color=discord.Color.blue()
        )
        if article.get('urlToImage'):
            embed.set_image(url=article.get('urlToImage'))
        
        source_name = article.get('source', {}).get('name', 'Unknown Source')
        embed.set_footer(text=f"Source: {source_name}")
        
        await ctx.send(embed=embed)

bot.run(DISCORD_TOKEN)

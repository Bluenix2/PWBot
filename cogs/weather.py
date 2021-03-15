import asyncio

import aiohttp
from discord.ext import commands


class UpdateWeather(commands.Cog):
    """Cog similiar to UpdateWhen but sends the weather of Newfoundland.

    Isolated for easy unloading.
    """

    def __init__(self, bot):
        self.bot = bot

        self.weather = None
        self.city_code = 6354959  # Newfoundland and Labrador

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    async def fetch_weather(self):
        if self.weather is not None:
            return self.weather

        params = {'id': self.city_code, 'appid': self.bot.weather_key, 'units': 'metric'}
        endpoint = 'https://api.openweathermap.org/data/2.5/weather'
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params) as response:
                self.weather = await response.json()

        async def cache():
            await asyncio.sleep(1200)
            self.weather = None

        asyncio.create_task(cache())
        return self.weather

    def caclulate_direction(self, degree):
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
        return directions[round((degree % 360) / 45)]

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect update related messages and respond with the weather."""
        if message.author.bot:
            return

        content_lower = message.content.lower()
        if 'update?' in content_lower or 'news' in content_lower and 'update' in content_lower:
            weather = await self.fetch_weather()

            string = "St. John's, NL - "
            string += f"Current Conditions: {weather['main']['temp']}°C, "
            string += f"Humidity: {weather['main']['humidity']} %, "
            string += f"Wind: {self.caclulate_direction(weather['wind']['deg'])} {weather['wind']['speed']} km/h, "
            string += f"Visibility: {round(weather['visibility'] / 1000)} km. "

            # First make a list of all descriptions, then loop through all descritpions
            # and make the first character capitalized.
            descs = [desc[0].upper() + desc[1:] for desc in [obj['description'] for obj in weather['weather']]]
            string += ', '.join(descs) + "."
            await message.channel.send(string)


def setup(bot):
    bot.add_cog(UpdateWeather(bot))

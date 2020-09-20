from discord.ext import commands


class _ContextDBAcquire:
    """Helper class allowing the use of context managers,

    asyncpg already implements the context manager protocol,
    but this uses the cached db connection attribute
    """

    __slots__ = ('ctx', 'timeout')

    def __init__(self, ctx, timeout):
        self.ctx = ctx
        self.timeout = timeout

    def __await__(self):
        return self.ctx._acquire(self.timeout).__await__()

    async def __aenter__(self):
        await self.ctx._acquire(self.timeout)
        return self.ctx.db

    async def __aexit__(self, *args):
        await self.ctx.release()


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool = self.bot.pool
        self._db = None

    @property
    def db(self):
        """Cached database connection"""
        return self._db if self._db else self.pool

    async def _acquire(self, timeout):
        if self._db is None:
            self._db = await self.pool.acquire(timeout=timeout)
        return self._db

    async def acquire(self, timeout=300.0):
        """Acquires a database connection from the pool.
        Implements both ::

            async with ctx.acquire():
                await ctx.db.execute(...)

        and: ::

            await ctx.acquire()
            try:
                await ctx.db.execute(...)
            finally:
                await ctx.release()
        """
        return _ContextDBAcquire(self, timeout)

    async def release(self):
        """Releases the database connection"""
        if self._db is not None:
            await self.pool.release(self._db)
            self._db = None

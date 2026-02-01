"""Load balancing utilities."""


import asyncio
from random import choice
from typing import Any, Callable, List

class LoadBalancer:

def __init__(self, workers: List[Callable]):

        self.workers = workers
        self.current = 0

    async def round_robin(self, *args, **kwargs) -> Any:
        """Round - robin load balancing."""
        worker = self.workers[self.current]
        self.current = (self.current + 1) % len(self.workers)
        return await worker(*args, **kwargs)

    async def random_choice(self, *args, **kwargs) -> Any:
        """Random worker selection."""
        worker = choice(self.workers)
        return await worker(*args, **kwargs)

    async def parallel_execution(self, *args, **kwargs) -> List[Any]:
        """Execute on all workers in parallel."""
        tasks = [worker(*args, **kwargs) for worker in self.workers]
        return await asyncio.gather(*tasks, return_exceptions=True)
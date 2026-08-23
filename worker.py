from rq import Queue
from redis import Redis
import os

# Este archivo ya no se usa por defecto; usamos `rq worker` en docker-compose.
# Lo queda para referencia.

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

print('Worker helper - use `rq worker` in production')

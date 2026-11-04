"""Forward localhost:8080 inside the workspace container to the Keycloak service.

Keycloak issues tokens for http://localhost:8080 (the address the host browser uses).
Inside the workspace, localhost:8080 is otherwise empty, so a browser or Playwright
running in the Dev Container could not reach the login page. This keeps one issuer
URL for host browsers, container browsers and the API. Runs as the workspace's main
process; the container stays up even if the forwarder fails.
"""

import asyncio
import os

LISTEN = ("127.0.0.1", 8080)
TARGET = (os.environ.get("KEYCLOAK_FORWARD_HOST", "keycloak"), 8080)


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        writer.close()


async def handle(
    client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
) -> None:
    try:
        upstream_reader, upstream_writer = await asyncio.open_connection(*TARGET)
    except OSError:
        client_writer.close()  # Keycloak not up yet; the browser simply retries.
        return
    await asyncio.gather(
        pipe(client_reader, upstream_writer), pipe(upstream_reader, client_writer)
    )


async def main() -> None:
    server = await asyncio.start_server(handle, *LISTEN)
    print(f"Forwarding {LISTEN[0]}:{LISTEN[1]} -> {TARGET[0]}:{TARGET[1]}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

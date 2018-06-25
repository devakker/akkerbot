
async def download_image_from_url(url, file_path):
    import aiohttp
    # TODO need headers to avoid 403
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            file_contents = await resp.read()
            with open(file_path, "wb") as f:
                f.write(file_contents)

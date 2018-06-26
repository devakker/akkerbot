
async def download_image_from_url(url, file_path):
    import aiohttp
    # TODO need to test if this avoids 403
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/50.0.2661.102 Safari/537.36'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            file_contents = await resp.read()
            with open(file_path, "wb") as f:
                f.write(file_contents)

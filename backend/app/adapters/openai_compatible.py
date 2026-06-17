import httpx

async def chat(endpoint: str, model: str, messages: list[dict], api_key: str | None = None, timeout: int = 120):
    headers={'Content-Type':'application/json'}
    if api_key:
        headers['Authorization']=f'Bearer {api_key}'
    url=endpoint.rstrip('/') + '/v1/chat/completions'
    payload={'model': model, 'messages': messages, 'stream': False}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data=r.json()
        return data['choices'][0]['message']['content']

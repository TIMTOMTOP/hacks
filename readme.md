```bash
 docker build -t sign-generator .
 docker run -p 8000:8000 --env-file .env sign-generator   
```

```bash
curl -s -X POST "http://localhost:8000/generate-sign" \
     -H "Content-Type: application/json" \
     -d '{"request_type": "initial", "content": "Create a broken elevator sign."}' | \
     jq '.content[0].text'  
```


```bash
curl -s -X POST "http://localhost:8000/generate-sign" \
     -H "Content-Type: application/json" \
     -d '{"request_type": "style_choice", "content": "1", "conversation_id": "0"}' | \
     jq -r '.content[0].text'

```
```bash
 docker build -t sign-generator .
 docker run -p 8000:8000 --env-file .env sign-generator   
```

```bash
curl -s -X POST "http://localhost:8000/generate-sign" \
     -H "Content-Type: application/json" \
     -d '{"request_type": "initial", "content": "..."}' | \
     jq '.content[0].text'  
```


```bash
curl -s -X POST "http://localhost:8000/generate-sign" \
     -H "Content-Type: application/json" \
     -d '{"request_type": "style_choice", "content": "1", "conversation_id": "0"}' | \
     jq -r '.content[0].text'

```

```bash
curl -X POST http://localhost:8000/analyze-brand-guidelines \
-H "Content-Type: application/json" \
-d '{
    "pdf_url": "https://dsgjssiyprmqymrpraxf.supabase.co/storage/v1/object/public/AAK//grafiskmanual-2.0.1-2024.pdf",
    "brand_name": "LUND"
}'

```
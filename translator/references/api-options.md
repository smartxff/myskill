# Translation API Options

## DeepL

Popular for high-quality translations, especially European languages.

**Configuration:**
```bash
python scripts/translate.py --config --provider deepl --api-key YOUR_API_KEY
```

**API Key:** Get from https://www.deepl.com/pro-api

## OpenAI (GPT)

Uses GPT models for translation with context awareness.

**Configuration:**
```bash
python scripts/translate.py --config --provider openai --api-key YOUR_API_KEY
```

**API Key:** Get from https://platform.openai.com/api-keys

## Google Translate

Free tier available, good for common language pairs.

## Microsoft Translator

Enterprise-grade translation service.

## Choosing a Provider

- **DeepL**: Best for European languages, high quality
- **OpenAI**: Best for context-aware translation, creative content
- **Google**: Good balance, extensive language support
- **Microsoft**: Enterprise features, good for formal documents

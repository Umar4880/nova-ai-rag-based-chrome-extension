# Chrome Extension Setup Guide

## Quick Start

### 1. Generate Icons (Required)

Before loading the extension, you need to create icon files:

**Option A: Use the Icon Generator (Quick)**
1. Open `icon-generator.html` in your browser
2. Click "Download All Icons"
3. Move the downloaded PNG files to `app/ui/icons/` folder

**Option B: Create Professional Icons (Recommended for Production)**
- Use Figma, Adobe Illustrator, or Canva
- Create 3 PNG files with transparent backgrounds:
  - `icon16.png` (16x16 pixels)
  - `icon48.png` (48x48 pixels)
  - `icon128.png` (128x128 pixels)
- Save them in `app/ui/icons/` folder

### 2. Load Extension in Chrome

1. Open Chrome browser
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top-right corner)
4. Click "Load unpacked"
5. Select the `app/ui` folder
6. Done! The extension is now installed

### 3. Start Backend API

Make sure your FastAPI backend is running:

```bash
cd chrome-extension
python -m uvicorn app.main:app --reload --port 8000
```

### 4. Test the Extension

1. Navigate to any website (e.g., https://example.com)
2. Look for the purple chat button at bottom-right
3. Click it to open the chatbot
4. Start chatting!

## File Checklist

Before loading the extension, ensure these files exist:

- ✅ `manifest.json` - Extension configuration
- ✅ `background.js` - Background service worker
- ✅ `content.js` - Chat UI injection script
- ✅ `styles.css` - Chat UI styles
- ✅ `popup.html` - Extension popup
- ✅ `popup.js` - Popup functionality
- ⚠️ `icons/icon16.png` - 16x16 icon (REQUIRED)
- ⚠️ `icons/icon48.png` - 48x48 icon (REQUIRED)
- ⚠️ `icons/icon128.png` - 128x128 icon (REQUIRED)

## Configuration

### Change API URL

If your backend is not on `localhost:8000`, update `background.js`:

```javascript
const API_BASE_URL = 'https://your-domain.com';
```

### Change Permissions

Edit `manifest.json` to add/remove permissions or change which sites the extension runs on.

## Features

- 🤖 AI chatbot appears on every webpage
- 🔄 Automatic session creation per tab
- 💬 Context-aware conversations
- 🗑️ Clear chat history
- 📱 Responsive design
- ⚡ Lightweight and fast

## Troubleshooting

### Extension won't load
- Make sure all icon files exist in `icons/` folder
- Check `manifest.json` is valid JSON
- Look for errors in `chrome://extensions/` page

### Chat button doesn't appear
- Check browser console (F12) for errors
- Verify content.js loaded (check Extensions page)
- Try refreshing the webpage

### Messages not sending
- Ensure backend API is running on correct port
- Check background service worker console:
  - Go to `chrome://extensions/`
  - Click "Details" on your extension
  - Click "Inspect views: service worker"
- Verify API_BASE_URL in background.js

### Session not creating
- Check background service worker console for errors
- Verify backend `/session/new` endpoint is working
- Check Network tab in DevTools for failed requests

## Publishing to Chrome Web Store

See `README.md` for detailed publishing instructions.

### Requirements:
1. Professional icons (not placeholders)
2. Privacy policy (if collecting data)
3. Screenshots (1280x800 or 640x400)
4. Detailed description
5. Developer account ($5 one-time fee)

## Next Steps

1. **Test thoroughly**: Try different websites, clear history, check error handling
2. **Improve icons**: Create professional-looking icons for production
3. **Add features**: Consider adding settings, themes, or keyboard shortcuts
4. **Prepare for production**: Update API URL, create privacy policy, gather screenshots
5. **Publish**: Submit to Chrome Web Store when ready

## Support

- Check browser console for errors
- Review Chrome extension documentation
- Test API endpoints separately
- Verify all files are in correct locations

Good luck with your Chrome extension! 🚀

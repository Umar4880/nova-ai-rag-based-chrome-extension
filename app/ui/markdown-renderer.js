/**
 * Markdown + Math renderer for LLM responses using third-party libraries
 * - Uses marked.js for markdown rendering
 * - Uses KaTeX for math rendering
 * - Preserves LaTeX math ($...$, $$...$$)
 * - Uses DOMPurify for HTML sanitization
 * 
 * Libraries are loaded via manifest.json as local files:
 * - lib/marked.min.js
 * - lib/katex.min.js
 * - lib/purify.min.js
 * - lib/katex.min.css
 */

// Verify libraries are loaded
(function checkLibraries() {
    const checkInterval = setInterval(() => {
        if (window.marked && window.katex && window.DOMPurify) {
            console.log('[MARKDOWN] All libraries loaded successfully');
            console.log('[MARKDOWN] marked:', typeof window.marked);
            console.log('[MARKDOWN] katex:', typeof window.katex);
            console.log('[MARKDOWN] DOMPurify:', typeof window.DOMPurify);
            clearInterval(checkInterval);
        }
    }, 100);
    
    // Timeout after 5 seconds
    setTimeout(() => {
        clearInterval(checkInterval);
        if (!window.marked) console.error('[MARKDOWN] marked.js not loaded');
        if (!window.katex) console.error('[MARKDOWN] KaTeX not loaded');
        if (!window.DOMPurify) console.error('[MARKDOWN] DOMPurify not loaded');
    }, 5000);
})();

class MarkdownRenderer {
    constructor(options = {}) {
        this.options = options;
        this.initMarked();
    }

    initMarked() {
        // Wait for marked to load
        const checkMarked = setInterval(() => {
            if (window.marked) {
                clearInterval(checkMarked);
                // Configure marked
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    headerIds: false,
                    mangle: false
                });
                console.log('[MARKDOWN] marked.js configured');
            }
        }, 100);
    }

    render(markdown) {
        if (!markdown) return '';

        // Extract and preserve math expressions before markdown processing
        const mathBlocks = [];
        let processed = markdown;

        // Extract display math ($$...$$)
        processed = processed.replace(/\$\$([\s\S]+?)\$\$/g, (match, expr) => {
            const placeholder = `{{MATH_DISPLAY_${mathBlocks.length}}}`;
            mathBlocks.push({ type: 'display', expr: expr.trim(), placeholder });
            return placeholder;
        });

        // Extract inline math ($...$)
        processed = processed.replace(/\$([^\$\n]+?)\$/g, (match, expr) => {
            const placeholder = `{{MATH_INLINE_${mathBlocks.length}}}`;
            mathBlocks.push({ type: 'inline', expr: expr.trim(), placeholder });
            return placeholder;
        });

        // Render markdown to HTML
        let html = '';
        if (window.marked) {
            try {
                html = marked.parse(processed);
            } catch (e) {
                console.error('[MARKDOWN] marked.parse failed:', e);
                html = this._fallbackRender(processed);
            }
        } else {
            console.warn('[MARKDOWN] marked not loaded, using fallback');
            html = this._fallbackRender(processed);
        }

        // Restore and render math expressions
        mathBlocks.forEach(({ type, expr, placeholder }) => {
            let rendered = '';
            if (window.katex) {
                try {
                    rendered = katex.renderToString(expr, {
                        displayMode: type === 'display',
                        throwOnError: false,
                        strict: false,
                        trust: false
                    });
                } catch (e) {
                    console.error('[MARKDOWN] KaTeX render failed:', e);
                    rendered = type === 'display' ? `<div class="math-error">$$${expr}$$</div>` : `<span class="math-error">$${expr}$</span>`;
                }
            } else {
                // Fallback: display as-is
                rendered = type === 'display' ? `<div class="math-fallback">$$${expr}$$</div>` : `<span class="math-fallback">$${expr}$</span>`;
            }
            html = html.replace(placeholder, rendered);
        });

        // Sanitize HTML
        if (window.DOMPurify) {
            html = DOMPurify.sanitize(html, {
                ADD_TAGS: ['math', 'semantics', 'mrow', 'msup', 'msub', 'mi', 'mo', 'mn', 'mfrac', 'msqrt', 'mtext', 'annotation'],
                ADD_ATTR: ['class', 'style', 'encoding']
            });
        }

        return html;
    }

    // Fallback renderer if marked.js not available
    _fallbackRender(text) {
        return text
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.+)$/gm, '<p>$1</p>');
    }

    renderStream(chunk, container) {
        if (!container) return;
        const rendered = this.render(chunk);
        const temp = document.createElement('div');
        temp.innerHTML = rendered;
        while (temp.firstChild) container.appendChild(temp.firstChild);
        container.scrollTop = container.scrollHeight;
    }

    typeset(container) {
        // KaTeX renders synchronously, no need for async typeset
        // This method kept for compatibility
        console.log('[MARKDOWN] Math rendering complete (KaTeX)');
    }
}

// Export for use in content script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownRenderer;
}


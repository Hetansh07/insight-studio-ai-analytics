"""
HTML templates for Vanna Agents servers.
"""

from typing import Optional


def get_vanna_component_script(
    dev_mode: bool = False,
    static_path: str = "/static",
    cdn_url: str = "https://img.vanna.ai/vanna-components.js",
) -> str:
    """Get the script tag for loading Vanna web components.

    Args:
        dev_mode: If True, load from local static files
        static_path: Path to static assets in dev mode
        cdn_url: CDN URL for production

    Returns:
        HTML script tag for loading components
    """
    if dev_mode:
        return (
            f'<script type="module" src="{static_path}/vanna-components.js"></script>'
        )
    else:
        return f'<script type="module" src="{cdn_url}"></script>'


def get_index_html(
    dev_mode: bool = False,
    static_path: str = "/static",
    cdn_url: str = "https://img.vanna.ai/vanna-components.js",
    api_base_url: str = "",
) -> str:
    """Generate index HTML with configurable component loading.

    Args:
        dev_mode: If True, load components from local static files
        static_path: Path to static assets in dev mode
        cdn_url: CDN URL for production components
        api_base_url: Base URL for API endpoints

    Returns:
        Complete HTML page as string
    """
    component_script = get_vanna_component_script(dev_mode, static_path, cdn_url)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insight Studio | Natural Language Data Insights</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        'vanna-navy': '#023d60',
                        'vanna-cream': '#e7e1cf',
                        'vanna-teal': '#15a8a8',
                        'vanna-orange': '#fe5d26',
                        'vanna-magenta': '#bf1363',
                    }},
                    fontFamily: {{
                        'sans': ['Space Grotesk', 'ui-sans-serif', 'system-ui'],
                        'serif': ['Roboto Slab', 'ui-serif', 'Georgia'],
                        'mono': ['Space Mono', 'ui-monospace', 'monospace'],
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background: #f4f8f8;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
            color: #023d60;
        }}

        /* Background decorations matching landing page */
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            /* Radial gradients with brand colors */
            background:
                radial-gradient(circle at 12% 5%, rgba(21, 168, 168, 0.13), transparent 34%),
                radial-gradient(circle at 92% 80%, rgba(254, 93, 38, 0.08), transparent 32%);
        }}

        body::after {{
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            background-image:
                linear-gradient(rgba(2, 61, 96, 0.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(2, 61, 96, 0.035) 1px, transparent 1px);
            background-size: 72px 72px;
        }}

        /* Ensure content is above background */
        body > * {{
            position: relative;
            z-index: 1;
        }}

        vanna-chat {{
            width: 100%;
            height: 100%;
            display: block;
        }}

        .app-shell {{
            max-width: 1220px;
            margin: 0 auto;
            padding: 24px 24px 40px;
        }}

        .brand-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 20px;
        }}

        .brand-mark {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #023d60;
        }}

        .brand-icon {{
            display: grid;
            place-items: center;
            width: 38px;
            height: 38px;
            border-radius: 11px;
            color: white;
            background: linear-gradient(145deg, #023d60, #15a8a8);
            box-shadow: 0 10px 22px -12px rgba(2, 61, 96, 0.65);
        }}

        .system-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border: 1px solid rgba(21, 168, 168, 0.24);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.72);
            color: #087f83;
            font: 700 11px/1 var(--vanna-font-family-default);
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .system-pill::before {{
            content: '';
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #20b486;
            box-shadow: 0 0 0 4px rgba(32, 180, 134, 0.13);
        }}

        .hero {{
            max-width: 720px;
            margin: 0 auto 20px;
            text-align: center;
        }}

        .hero h1 {{
            margin: 0;
            color: #023d60;
            font: 700 clamp(1.9rem, 3.4vw, 3rem)/1.02 "Roboto Slab", Georgia, serif;
            letter-spacing: -0.045em;
        }}

        .hero p {{
            margin: 10px auto 0;
            max-width: 620px;
            color: #526b78;
            font-size: 15px;
            line-height: 1.5;
        }}

        .panel {{
            border: 1px solid rgba(2, 61, 96, 0.12);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 22px 60px -38px rgba(2, 61, 96, 0.55);
            backdrop-filter: blur(12px);
        }}

        #loggedInStatus {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 10px 14px !important;
            margin: 0 auto 16px !important;
            max-width: 420px;
            font-size: 13px;
        }}

        #loggedInStatus br {{ display: none; }}
        #loggedInStatus button {{ margin-top: 0 !important; }}

        #configurationPanel {{
            max-width: 520px;
            padding: 16px !important;
            margin-bottom: 16px !important;
        }}

        .chat-launcher {{
            position: fixed;
            right: 24px;
            bottom: 24px;
            z-index: 20;
            width: 52px;
            height: 52px;
            border: 0;
            border-radius: 50%;
            background: #023d60;
            color: white;
            font-size: 21px;
            box-shadow: 0 12px 28px rgba(2, 61, 96, 0.28);
            cursor: pointer;
        }}

        .chat-launcher:hover {{ background: #15a8a8; }}

        .chat-popup {{
            position: fixed;
            right: 24px;
            bottom: 24px;
            z-index: 19;
            width: min(420px, calc(100vw - 32px));
            height: min(600px, calc(100vh - 32px));
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(2, 61, 96, 0.18);
            border-radius: 18px;
            background: white;
            box-shadow: 0 24px 70px rgba(2, 61, 96, 0.28);
        }}

        .chat-popup.hidden {{ display: none; }}

        .chat-popup-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background: #023d60;
            color: white;
            font-weight: 600;
        }}

        .chat-popup-actions {{ display: flex; gap: 6px; }}
        .chat-popup-actions button {{
            width: 28px;
            height: 28px;
            border: 1px solid rgba(255,255,255,.35);
            border-radius: 50%;
            background: transparent;
            color: white;
            cursor: pointer;
        }}
        .chat-popup > .panel {{ flex: 1; min-height: 0; display: flex; flex-direction: column; border: 0; border-radius: 0; padding: 0; overflow: hidden; }}
        .chat-popup vanna-chat {{ flex: 1; min-height: 0; height: 100%; max-width: none; border: 0; border-radius: 0; box-shadow: none; }}

        @media (max-width: 640px) {{
            .chat-launcher {{ right: 16px; bottom: 16px; }}
            .chat-popup {{ right: 8px; bottom: 8px; width: calc(100vw - 16px); height: calc(100vh - 16px); }}
        }}

        @media (max-width: 640px) {{
            .app-shell {{ padding: 18px 12px 28px; }}
            .brand-bar {{ margin-bottom: 22px; }}
            .system-pill {{ font-size: 9px; }}
        }}
    </style>
    {component_script}
</head>
<body>
    <div class="app-shell">
        <div class="brand-bar">
            <div class="brand-mark">
                <span class="brand-icon" aria-hidden="true">↗</span>
                <span>Insight Studio</span>
            </div>
            <div class="system-pill">Analysis workspace</div>
        </div>

        <div class="hero">
            <h1>Ask your data better questions.</h1>
            <p>Turn natural language into clear SQL-backed answers, tables, and visual insights from one focused workspace.</p>
        </div>

        <!-- Login Form -->
        <div id="loginContainer" class="panel max-w-md mx-auto mb-10 p-8">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-semibold text-vanna-navy mb-2 font-serif">Login to Continue</h2>
                <p class="text-sm text-slate-600">Select your email to access the chat</p>
            </div>

            <div class="mb-5">
                <label for="emailInput" class="block mb-2 text-sm font-medium text-vanna-navy">Email Address</label>
                <select
                    id="emailInput"
                    class="w-full px-4 py-3 text-sm border border-vanna-teal/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-vanna-teal focus:border-transparent bg-white"
                >
                    <option value="">Select an email...</option>
                    <option value="admin@example.com">admin@example.com</option>
                    <option value="user@example.com">user@example.com</option>
                </select>
            </div>

            <button id="loginButton" class="w-full px-4 py-3 bg-vanna-teal text-white text-sm font-medium rounded-lg hover:bg-vanna-navy focus:outline-none focus:ring-2 focus:ring-vanna-teal focus:ring-offset-2 transition disabled:bg-gray-400 disabled:cursor-not-allowed">
                Continue
            </button>

            <div class="mt-5 p-3 bg-vanna-teal/10 border-l-4 border-vanna-teal rounded text-xs text-vanna-navy leading-relaxed">
                <strong>Demo Mode:</strong> This is a frontend-only authentication demo.
                Your email will be stored as a cookie and automatically sent with all API requests.
            </div>
        </div>

        <!-- Logged In Status (hidden by default) -->
        <div id="loggedInStatus" class="hidden panel text-center p-4 mb-5">
            Logged in as <span id="loggedInEmail" class="font-semibold text-vanna-navy"></span>
            <br>
            <button id="logoutButton" class="mt-2 px-3 py-1.5 bg-vanna-navy text-white text-xs rounded hover:bg-vanna-teal transition">
                Logout
            </button>
        </div>

        <div id="configurationPanel" class="hidden panel max-w-md mx-auto mb-8 p-6">
            <h2 class="text-xl font-semibold text-vanna-navy mb-2 font-serif">Configure Google AI Studio</h2>
            <p class="text-sm text-slate-600 mb-4">Your key is sent to this server over the current connection and kept only in server memory. It is never displayed or saved.</p>
            <label for="geminiApiKey" class="block mb-2 text-sm font-medium text-vanna-navy">Gemini API key</label>
            <input id="geminiApiKey" type="password" autocomplete="off" class="w-full px-4 py-3 text-sm border border-vanna-teal/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-vanna-teal" placeholder="Paste your Google AI Studio key">
            <button id="configureGeminiButton" class="mt-4 w-full px-4 py-3 bg-vanna-teal text-white text-sm font-medium rounded-lg hover:bg-vanna-navy transition">Configure Gemini</button>
            <p id="configurationStatus" class="mt-3 text-sm text-slate-600" role="status"></p>
        </div>

        <!-- Chat Container (hidden by default) -->
        <div id="chatSections" class="hidden">
            <data-quality-dashboard api-base="{api_base_url}" initial-dataset="Customer"></data-quality-dashboard>
            <button id="chatLauncher" class="chat-launcher" title="Ask AI about your data" aria-label="Ask AI about your data">✦</button>
            <div id="chatPopup" class="chat-popup hidden" role="dialog" aria-label="AI Data Assistant">
                <div class="chat-popup-header">
                    <span>AI Data Assistant</span>
                    <div class="chat-popup-actions">
                        <button id="chatMinimize" title="Minimize chat" aria-label="Minimize chat">−</button>
                        <button id="chatClose" title="Close chat" aria-label="Close chat">×</button>
                    </div>
                </div>
                <div class="panel">
                <vanna-chat
                    title="AI Data Assistant"
                    hide-header
                    placeholder="Ask anything about your data..."
                    api-base="{api_base_url}"
                    sse-endpoint="{api_base_url}/api/vanna/v2/chat_sse"
                    ws-endpoint="{api_base_url}/api/vanna/v2/chat_websocket"
                    poll-endpoint="{api_base_url}/api/vanna/v2/chat_poll">
                </vanna-chat>
                </div>
            </div>
            <div id="responseFallback" class="hidden mt-4 p-5 bg-white rounded-lg shadow border border-vanna-teal/30">
                <h3 class="text-sm font-semibold text-vanna-navy mb-2">Response</h3>
                <div id="responseFallbackText" class="text-slate-700 whitespace-pre-wrap"></div>
            </div>

        </div>
    </div>

    <script>
        // Cookie helpers
        const getCookie = (name) => {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            return parts.length === 2 ? parts.pop().split(';').shift() : null;
        }};

        const setCookie = (name, value) => {{
            const expires = new Date(Date.now() + 365 * 864e5).toUTCString();
            document.cookie = `${{name}}=${{value}}; expires=${{expires}}; path=/; SameSite=Lax`;
        }};

        const deleteCookie = (name) => {{
            document.cookie = `${{name}}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        }};

        // Login/Logout
        document.addEventListener('DOMContentLoaded', () => {{
            const loginContainer = document.getElementById('loginContainer');
            const loggedInStatus = document.getElementById('loggedInStatus');
            const configurationPanel = document.getElementById('configurationPanel');
            const chatSections = document.getElementById('chatSections');
            const chatLauncher = document.getElementById('chatLauncher');
            const chatPopup = document.getElementById('chatPopup');
            const chatMinimize = document.getElementById('chatMinimize');
            const chatClose = document.getElementById('chatClose');
            const vannaChatElement = document.querySelector('vanna-chat');
            if (vannaChatElement) vannaChatElement.showProgress = false;
            const emailInput = document.getElementById('emailInput');
            const loginButton = document.getElementById('loginButton');
            const logoutButton = document.getElementById('logoutButton');
            const loggedInEmail = document.getElementById('loggedInEmail');
            const geminiApiKey = document.getElementById('geminiApiKey');
            const configureGeminiButton = document.getElementById('configureGeminiButton');
            const configurationStatus = document.getElementById('configurationStatus');
            const email = getCookie('vanna_email');

            // Check if already logged in
            if (email) {{
                loginContainer.classList.add('hidden');
                loggedInStatus.classList.remove('hidden');
                chatSections.classList.remove('hidden');
                loggedInEmail.textContent = email;
                configurationPanel.classList.toggle('hidden', email !== 'admin@example.com');
            }}

            // Login button
            loginButton.addEventListener('click', () => {{
                const email = emailInput.value.trim();
                if (!email) {{
                    alert('Please select an email address');
                    return;
                }}
                setCookie('vanna_email', email);
                loginContainer.classList.add('hidden');
                loggedInStatus.classList.remove('hidden');
                chatSections.classList.remove('hidden');
                loggedInEmail.textContent = email;
                configurationPanel.classList.toggle('hidden', email !== 'admin@example.com');
            }});

            // Logout button
            logoutButton.addEventListener('click', () => {{
                deleteCookie('vanna_email');
                loginContainer.classList.remove('hidden');
                loggedInStatus.classList.add('hidden');
                chatSections.classList.add('hidden');
                chatPopup.classList.add('hidden');
                configurationPanel.classList.add('hidden');
                emailInput.value = '';
            }});

            const openChat = () => {{
                chatPopup.classList.remove('hidden');
                chatLauncher.classList.add('hidden');
            }};
            const closeChat = () => {{
                chatPopup.classList.add('hidden');
                chatLauncher.classList.remove('hidden');
            }};
            chatLauncher.addEventListener('click', openChat);
            chatMinimize.addEventListener('click', closeChat);
            chatClose.addEventListener('click', closeChat);

            configureGeminiButton.addEventListener('click', async () => {{
                const apiKey = geminiApiKey.value.trim();
                if (!apiKey) {{
                    configurationStatus.textContent = 'Enter a Gemini API key first.';
                    return;
                }}
                configureGeminiButton.disabled = true;
                configurationStatus.textContent = 'Configuring...';
                try {{
                    const response = await fetch('{api_base_url}/api/vanna/v2/configure/gemini', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        credentials: 'same-origin',
                        body: JSON.stringify({{ api_key: apiKey }})
                    }});
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || 'Configuration failed');
                    geminiApiKey.value = '';
                    configurationStatus.textContent = 'Gemini configured for this server session.';
                }} catch (error) {{
                    configurationStatus.textContent = error instanceof Error ? error.message : 'Configuration failed.';
                }} finally {{
                    configureGeminiButton.disabled = false;
                }}
            }});

            // Enter key
            emailInput.addEventListener('keypress', (e) => {{
                if (e.key === 'Enter') loginButton.click();
            }});
        }});
    </script>

    <script>
        // Artifact demo event listener
        document.addEventListener('DOMContentLoaded', () => {{
            const vannaChat = document.querySelector('vanna-chat');
            const responseFallback = document.getElementById('responseFallback');
            const responseFallbackText = document.getElementById('responseFallbackText');

            if (vannaChat && responseFallback && responseFallbackText) {{
                vannaChat.addEventListener('chunk-received', (event) => {{
                    const chunk = event.detail?.chunk;
                    const rich = chunk?.rich;
                    if (rich?.type === 'text' && rich.content) {{
                        responseFallbackText.textContent = rich.content;
                        responseFallback.classList.remove('hidden');
                    }}
                }});

                // Add artifact event listener to demonstrate external rendering
                vannaChat.addEventListener('artifact-opened', (event) => {{
                    const {{ artifactId, type, title, trigger }} = event.detail;

                    console.log('🎨 Artifact Event:', {{ artifactId, type, title, trigger }});

                    // For demo: open all artifacts externally
                    setTimeout(() => {{
                        const newWindow = window.open('', '_blank', 'width=900,height=700');
                        if (newWindow) {{
                            newWindow.document.write(event.detail.getStandaloneHTML());
                            newWindow.document.close();
                            newWindow.document.title = title || 'Vanna Artifact';
                            console.log(`📱 Opened ${{title}} in new window`);
                        }}
                    }}, 100);

                    // Prevent default in-chat rendering
                    event.detail.preventDefault();
                    console.log('✋ Showing placeholder in chat instead of full artifact');
                }});

                console.log('🎯 Artifact demo mode: All artifacts will open externally');
            }}
        }});

        // Fallback if web component doesn't load
        if (!customElements.get('vanna-chat')) {{
            setTimeout(() => {{
                if (!customElements.get('vanna-chat')) {{
                    document.querySelector('vanna-chat').innerHTML = `
                        <div class="p-10 text-center text-gray-600">
                            <h3 class="text-xl font-semibold mb-2">Vanna Chat Component</h3>
                            <p class="mb-2">Web component failed to load. Please check your connection.</p>
                            <p class="text-sm text-gray-400">
                                {("Loading from: local static assets" if dev_mode else f"Loading from: {cdn_url}")}
                            </p>
                        </div>
                    `;
                }}
            }}, 2000);
        }}
    </script>
</body>
</html>"""


# Backward compatibility - default production HTML
INDEX_HTML = get_index_html()

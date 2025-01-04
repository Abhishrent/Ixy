import discord
from discord.ext import commands
import io
import re
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_BREAK
import pygments.util
import subprocess


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command('hl', help='Highlights the code provided in the attached file.')
    async def highlight_code(self, ctx):
        # Ensure the user provided a file attachment
        if len(ctx.message.attachments) == 0:
            await ctx.send("Please provide a code file.")
            return

        # Get the first attachment (file)
        attachment = ctx.message.attachments[0]

        try:
            # Download the file
            file_content = await attachment.read()
            
            # Try to detect the correct lexer based on the file's extension
            try:
                lexer = get_lexer_for_filename(attachment.filename)
            except pygments.util.ClassNotFound:
                # Default to plain text if no lexer is found
                lexer = TextLexer()

            # Custom CSS with improved color schemes for both modes
            custom_css = """
            <style>
                :root {
                    --dark-bg: #1e1e1e;
                    --dark-text: #d4d4d4;
                    --light-bg: #ffffff;
                    --light-text: #000000;
                }

                body {
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    margin: 0;
                    padding: 20px;
                    transition: all 0.3s ease;
                    min-height: 100vh;
                }

                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }

                .header {
                    position: sticky;
                    top: 0;
                    padding: 10px 0;
                    margin-bottom: 20px;
                    z-index: 1000;
                    backdrop-filter: blur(10px);
                }

                #mode-toggle {
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.2s ease;
                }

                pre {
                    padding: 20px;
                    border-radius: 8px;
                    overflow-x: auto;
                    font-size: 14px;
                    line-height: 1.5;
                }

                /* Dark Mode */
                body.dark-mode {
                    background-color: var(--dark-bg);
                    color: var(--dark-text);
                }

                .dark-mode #mode-toggle {
                    background-color: #4a4a4a;
                    color: #ffffff;
                }

                .dark-mode #mode-toggle:hover {
                    background-color: #5a5a5a;
                }

                .dark-mode pre {
                    background-color: #252525;
                    border: 1px solid #333;
                }

                /* Light Mode */
                body.light-mode {
                    background-color: var(--light-bg);
                    color: var(--light-text);
                }

                .light-mode #mode-toggle {
                    background-color: #e0e0e0;
                    color: #000000;
                }

                .light-mode #mode-toggle:hover {
                    background-color: #d0d0d0;
                }

                .light-mode pre {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                }

                /* Syntax Highlighting Overrides */
                .dark-mode .highlight .k { color: #569cd6; } /* Keyword */
                .dark-mode .highlight .s { color: #ce9178; } /* String */
                .dark-mode .highlight .c1 { color: #6A9955; } /* Comment */
                .dark-mode .highlight .n { color: #9cdcfe; } /* Name */
                .dark-mode .highlight .o { color: #d4d4d4; } /* Operator */

                .light-mode .highlight .k { color: #0000ff; } /* Keyword */
                .light-mode .highlight .s { color: #a31515; } /* String */
                .light-mode .highlight .c1 { color: #008000; } /* Comment */
                .light-mode .highlight .n { color: #001080; } /* Name */
                .light-mode .highlight .o { color: #000000; } /* Operator */
            </style>
            """

            # JavaScript for mode toggling with preference saving
            custom_js = """
            <script>
                function setMode(mode) {
                    const body = document.body;
                    const toggle = document.getElementById('mode-toggle');
                    
                    body.className = mode;
                    toggle.textContent = `Switch to ${mode === 'dark-mode' ? 'Light' : 'Dark'} Mode`;
                    
                    localStorage.setItem('preferredMode', mode);
                }

                function toggleMode() {
                    const currentMode = document.body.classList.contains('dark-mode') ? 'light-mode' : 'dark-mode';
                    setMode(currentMode);
                }

                // Initialize mode based on saved preference or system preference
                document.addEventListener('DOMContentLoaded', () => {
                    const savedMode = localStorage.getItem('preferredMode');
                    if (savedMode) {
                        setMode(savedMode);
                    } else {
                        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                        setMode(prefersDark ? 'dark-mode' : 'light-mode');
                    }
                });
            </script>
            """

            # Create HTML template
            html_template = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Formatted Code</title>
                {custom_css}
                {custom_js}
            </head>
            <body class="dark-mode">
                <div class="container">
                    <div class="header">
                        <button id="mode-toggle" onclick="toggleMode()">Switch to Light Mode</button>
                    </div>
                    <div class="code-container">
                        {highlight(file_content.decode('utf-8', errors='replace'), lexer, HtmlFormatter(style='monokai'))}
                    </div>
                </div>
            </body>
            </html>
            """

            # Create an in-memory file-like object to store the HTML content
            html_output = io.BytesIO(html_template.encode('utf-8'))
            
            # Send the HTML file as a Discord attachment
            await ctx.send(
                "Here's your formatted code! Download and open in a browser to view the code with proper syntax highlighting:",
                file=discord.File(html_output, filename=f"formatted_{attachment.filename}.html")
            )

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


async def setup(bot):
    await bot.add_cog(Utils(bot))

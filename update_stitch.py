import re
import json

# 1. Read the stitch_home.html
with open('stitch_home.html', 'r') as f:
    html_content = f.read()

# 2. Extract the tailwind config script
tailwind_match = re.search(r'<script id="tailwind-config">\s*tailwind\.config\s*=\s*({.*?})\s*</script>', html_content, re.DOTALL)
if tailwind_match:
    tw_config_str = tailwind_match.group(1)
    # inject corePlugins preflight false
    tw_config_str = tw_config_str.replace('"darkMode": "class",', '"corePlugins": { "preflight": false },\n        "darkMode": "class",')
else:
    print("Could not find tailwind config!")
    tw_config_str = "tailwind.config = { corePlugins: { preflight: false } }"

# 3. Update index.html
with open('frontend/index.html', 'r') as f:
    index_html = f.read()

head_additions = """
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;600&family=Hanken+Grotesk:wght@600;700&family=Inter:wght@400&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <script>
      tailwind.config = """ + tw_config_str + """
    </script>
"""

if "cdn.tailwindcss.com" not in index_html:
    index_html = index_html.replace('</head>', head_additions + '\n  </head>')
    with open('frontend/index.html', 'w') as f:
        f.write(index_html)

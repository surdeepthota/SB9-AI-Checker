import re

with open('stitch_home_v2.html', 'r') as f:
    html_content = f.read()

# 1. Extract the tailwind config script
tailwind_match = re.search(r'<script id="tailwind-config">\s*tailwind\.config\s*=\s*({.*?})\s*</script>', html_content, re.DOTALL)
if tailwind_match:
    tw_config_str = tailwind_match.group(1)
    tw_config_str = tw_config_str.replace('"darkMode": "class",', '"corePlugins": { "preflight": false },\n        "darkMode": "class",')
    
    # Update index.html
    with open('frontend/index.html', 'r') as f:
        index_html = f.read()
    
    # Replace the existing tailwind config script
    index_html = re.sub(r'<script>\s*tailwind\.config\s*=\s*{.*?}\s*</script>', '<script>\n      tailwind.config = ' + tw_config_str + '\n    </script>', index_html, flags=re.DOTALL)
    with open('frontend/index.html', 'w') as f:
        f.write(index_html)

# 2. Extract <main> and <style>
main_match = re.search(r'(<main.*?</main>)', html_content, re.DOTALL)
style_match = re.search(r'(<style>.*?</style>)', html_content, re.DOTALL)

if main_match:
    main_content = main_match.group(1)
    # Convert HTML to JSX
    main_content = main_content.replace('class=', 'className=')
    main_content = re.sub(r'style="([^"]*)"', lambda m: 'style={{ ' + ', '.join([f"'{k.strip()}': '{v.strip()}'" for k, v in [p.split(':') for p in m.group(1).split(';') if p.strip()]]) + ' }}', main_content)
    # Fix self-closing tags
    main_content = main_content.replace('<img>', '<img/>').replace('<input>', '<input/>').replace('<hr>', '<hr/>').replace('<br>', '<br/>')
    
    # Also replace <!-- comments --> with {/* comments */}
    main_content = re.sub(r'<!--(.*?)-->', r'{/*\1*/}', main_content, flags=re.DOTALL)
    
    style_content = style_match.group(1) if style_match else ''
    style_content = style_content.replace('<style>', '<style>{`').replace('</style>', '`}</style>')

    jsx_code = f"""import React from 'react';
import {{ Link }} from 'react-router-dom';

function Home() {{
  return (
    <>
      {style_content}
      {main_content}
    </>
  );
}}

export default Home;
"""
    # Just a small fix for Link
    jsx_code = jsx_code.replace('<button className="bg-primary text-on-primary font-headline-md text-headline-md text-[18px] px-8 py-3 rounded-md hover:bg-primary-fixed-dim transition-colors active:scale-95 w-full max-w-[280px]">', '<Link to="/check" className="bg-primary text-on-primary font-headline-md text-headline-md text-[18px] px-8 py-3 rounded-md hover:bg-primary-fixed-dim transition-colors active:scale-95 w-full max-w-[280px] inline-flex justify-center items-center no-underline">')
    jsx_code = jsx_code.replace('Start Analyzing\n            </button>', 'Start Analyzing\n            </Link>')

    with open('frontend/src/pages/Home.jsx', 'w') as f:
        f.write(jsx_code)

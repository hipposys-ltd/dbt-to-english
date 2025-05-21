
import streamlit as st
import requests
import json
import re
from io import BytesIO


def split_diagram_block(text):
    pattern = re.compile(r"(.*?)graph TD(.*?)```(.*)", re.DOTALL)
    match = pattern.match(text)
    if match:
        before = match.group(1).strip()
        diagram = "graph TD\n" + match.group(2).strip() + \
            ""
        after = match.group(3).strip()
        return [
            {'type': 'prompt', 'text': before},
            {'type': 'diagram', 'text': diagram},
            {'type': 'prompt', 'text': after}]
    else:
        return [{'type': 'prompt', 'text': text}]


def get_chat_response(catalog_file, manifest_file, node_to_parse, prompt,
                      additional_context_file):
    url = 'http://fastapi:8080/get_node_in_english'
    with requests.post(
            url,
            stream=True,
            files={'catalog_file': catalog_file,
                   'manifest_file': manifest_file,
                   'additional_context_file': additional_context_file},
            data={'node_to_parse': node_to_parse,
                  'prompt': prompt}
            ) as response:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                parsed_chunk = str(chunk, encoding="utf-8")
                yield parsed_chunk


def download_github_file(github_url, save_path=None):
    if "github.com" in github_url \
       and "raw.githubusercontent.com" not in github_url:
        github_url = github_url.replace("github.com",
                                        "raw.githubusercontent.com")
        github_url = github_url.replace("blob/", "")
    response = requests.get(github_url)
    if response.status_code == 200:
        if save_path:
            # Save the content to a file
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return f"File saved to {save_path}"
        else:
            file_obj = BytesIO(response.content)
            file_obj.name = github_url.rsplit('/', 1)[1]
            return file_obj
    else:
        return f"Error: {response.status_code}"


def add_markdown(block):
    if block["type"] == "prompt":
        st.markdown(block["text"])
    else:
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true }});
            </script>
            <script src="https://cdn.jsdelivr.net/npm/panzoom@9.4.0/dist/panzoom.min.js"></script>
            <style>
                #mermaid-container {{
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    border: 1px solid #ccc;
                }}
                #mermaid-zoom {{
                    width: 100%;
                    height: 100%;
                }}
            </style>
        </head>
        <body>
            <div id="mermaid-container">
                <div id="mermaid-zoom">
                    <div class="mermaid">
                        {block["text"]}
                    </div>
                </div>
            </div>
            <script>
                const zoomElement = document.getElementById('mermaid-zoom');
                panzoom(zoomElement, {{
                    zoomSpeed: 0.065,
                    maxZoom: 5,
                    minZoom: 0.5
                }});
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=300)


with st.form("user_form"):
    catalog_file = st.file_uploader("Upload Catalog",
                                    type=['json'])
    manifest_file = st.file_uploader("Upload Manifest",
                                     type=["json"])
    github_link = st.text_input(
        label='Alternatively, enter the GitHub repository path containing manifest and catalog files',
        placeholder='https://github.com/hipposys-ltd/dbt-to-english/tree/main/DbtExampleProject/target')
    with open('streamlit/default_prompt.txt', 'r') as f:
        default_prompt = f.read()
    nodes_to_parse = []
    if manifest_file or github_link:
        if github_link:
            catalog_file = download_github_file(github_link + '/catalog.json')
            manifest_file = download_github_file(
                github_link + '/manifest.json')
        json_data = json.load(manifest_file)
        keys = list(json_data['nodes'].keys())
        nodes_to_parse = st.multiselect("Select a node id",
                                        [key for key in keys
                                         if key.split('.')[0] == 'model'])
        manifest_file.seek(0)
        prompt = st.text_area("System Prompt",
                              value=default_prompt,
                              height=200)
        additional_context = st.file_uploader("Upload Additional Context",
                                              type=['docx',
                                                    'pdf',
                                                    'txt',
                                                    'md'])
    submitted = st.form_submit_button("Parse Json Files" if not manifest_file
                                      and not github_link
                                      else "Run LLM")

if submitted:
    if ((catalog_file and manifest_file) or github_link) and nodes_to_parse:
        for node_to_parse in nodes_to_parse:
            blocks = []
            with st.expander(node_to_parse):
                with st.empty():
                    response = st.write_stream(
                        get_chat_response(catalog_file, manifest_file,
                                          node_to_parse, prompt,
                                          additional_context))
                    manifest_file.seek(0)
                    catalog_file.seek(0)
                    if additional_context:
                        additional_context.seek(0)
                    blocks = split_diagram_block(response)
                    add_markdown(blocks[0])
                if len(blocks) > 1:
                    for block in blocks[1:]:
                        add_markdown(block)
                # st.write(blocks)
                manifest_file.seek(0)
                catalog_file.seek(0)
                if additional_context:
                    additional_context.seek(0)
    else:
        st.warning("Please upload files before submitting and add node id.")

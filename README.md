# ⚠️ REPOSITORY MOVED - NO LONGER MAINTAINED HERE

**This repository has been transferred to new ownership and is no longer actively maintained in this location.**

## 🔄 Migration Notice

This repository and all associated open-source packages have been moved to a new GitHub organization.

**New Location:** https://github.com/ponderedw

## 📍 What This Means

- ✅ **Active development** continues at the new location
- ✅ **Latest updates** and releases are published there
- ✅ **Issues and pull requests** should be submitted to the new repository
- ⚠️ **This repository** will no longer receive updates

## 🔗 Find the Updated Repository

Please visit https://github.com/ponderedw to:
- Access the latest version of this package
- Report issues or contribute
- View updated documentation
- Get support from the maintainers

---

**Thank you for your understanding during this transition.**

# DBT to English

LLM-Powered Insights into Your DBT Project

## Overview

DBT to English is a tool that leverages large language models to provide human-friendly insights into your DBT project. It translates complex SQL logic, metadata, and lineage into clear, contextual explanations that are accessible to everyone on your team - whether they're developers, analysts, product managers, or engineers.

The tool goes beyond what DBT Docs and DBT Cloud's Explore offer by providing:

- Natural language explanations of model logic
- Query-level lineage visualization
- Detailed explanations of column derivations
- Dependency insights with brief explanations
- Customizable output through system prompts

## Features

- **Model Interpretation**: Get plain-English explanations of what your DBT models are doing
- **Interactive Lineage**: Visualize not just model-level connections but also internal relationships like CTEs
- **SQL Logic Translation**: Understand how each column is derived, including its source tables
- **Dependency Insights**: See brief explanations for each dependency
- **Customizable Output**: Modify the system prompt to change the structure, formatting, and style of the output
- **Multiple LLM Support**: Works with Anthropic and Amazon Bedrock models

## Project Setup  

### Getting Started  

1. Clone the repository:
   ```sh
   git clone https://github.com/hipposys-ltd/dbt-to-english
   cd dbt-to-english
   ```

2. Copy the environment template file:  
   ```sh
   cp private.env-template private.env
   ```

3. Open private.env and add your AWS credentials if you use Bedrock:
    ```
    AWS_ACCESS_KEY_ID=your-access-key  
    AWS_SECRET_ACCESS_KEY=your-secret-key  
    AWS_REGION=your-region  
    ```

    If using Anthropic, add your API key instead:
    ```
    ANTHROPIC_API_KEY=
    ```

4. If you're using a different AWS Bedrock model, update the LLM_MODEL variable in private.env. If using Anthropic, uncomment the LLM_MODEL variable with `Anthropic` prefix and specify the desired model.

## Running the Project

Start the project using Docker Compose:

```
docker compose up --build
```

## UI

Visit [http://localhost:8501/](http://localhost:8501/) to access the Streamlit interface.

1. Upload both `catalog.json` and `manifest.json`.  
   If you don't have a DBT project, you can use the sample files from `DbtExampleProject/target`.

2. Click the **"Parse JSON File"** button.

3. A new dropdown field labeled **"Select a node ID"** will appear. Choose the node(s) you want to parse.

4. Click the **"Run LLM"** button to generate the explanation.

5. The output will include:
   - A natural language description of the model
   - An interactive graph showing lineage at both the model and query level
   - SQL logic and calculations explaining how each column is derived
   - A columns table with detailed information
   - A dependencies table with brief explanations

6. You can customize the output by modifying the System Prompt field. This allows you to change the structure, add instructions, or rearrange the output to fit your team's needs.

## Backend

The Streamlit UI communicates with a FastAPI backend. It uses the `/get_node_in_english` endpoint, which can also be used independently of Streamlit.

### Endpoint: `/get_node_in_english`

**Parameters:**
- `catalog_file`
- `manifest_file`
- `node_to_parse`
- `prompt`

This endpoint processes the provided inputs and returns a natural language interpretation of the selected node.

## Important Notes

When modifying the system prompt, keep the diagram-related instructions as-is, especially the example section. The UI relies on this example to recognize the diagram portion in the LLM response and render it as an interactive graph.

## Contributing

We welcome contributions to this open-source project! Whether you're interested in adding new features, supporting more LLM providers, improving prompts, or enhancing the UI, your feedback and contributions will help shape the future of how we understand and interact with modern data stacks.

Please feel free to submit pull requests or share your ideas through issues.

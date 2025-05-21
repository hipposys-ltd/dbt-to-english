from langchain_aws import ChatBedrock
from langchain_anthropic import ChatAnthropic
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.prebuilt import create_react_agent
from langchain import hub
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, ToolMessage, AIMessage, AIMessageChunk
import os


class DbtToEnglish:
    def __init__(self, dbt_manifest, dbt_catalog,
                 node_id, prompt, additional_context, use_database):
        self._llm = None
        self.dbt_manifest = dbt_manifest
        self.dbt_catalog = dbt_catalog
        self.node_id = node_id
        self._system_message = None
        self.custom_prompt = prompt
        self.max_level = 2
        self._messages = None
        self.additional_context = additional_context
        self.use_database = use_database

    @property
    def sys_messages(self):
        # prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        # system_message = prompt_template.format(dialect="postgres", top_k=5)
        # sys_message = system_message + '\n' \
        #     + self.custom_prompt + '\n' + self.additional_context
        sys_message = self.custom_prompt + '\n' + self.additional_context
        return sys_message

    @property
    def db(self):
        db = SQLDatabase.from_uri(os.environ.get('DATABASE_URI'))
        return db

    @property
    def llm(self):
        model_type, model_id = os.environ.get('LLM_MODEL').split(':', 1)
        if model_type == 'Bedrock':
            self._llm = ChatBedrock(
                model_id=model_id,
                model_kwargs=dict(temperature=0, max_tokens=8192,),
            )
        elif model_type == 'Anthropic':
            self._llm = ChatAnthropic(
                model=model_id,
                temperature=0,
                max_tokens=8192,
            )
        return self._llm

    @property
    def sql_db_tool(self):
        return QuerySQLDatabaseTool(db=self.db)

    @property
    def llm_tools(self):
        tools = []
        if self.use_database:
            tools.append(self.sql_db_tool)
        return tools

    @property
    def react_agent(self):
        return create_react_agent(self.llm,
                                  tools=self.llm_tools,
                                  prompt=self.sys_messages
                                  )

    @staticmethod
    def upload_dbt_node(node, dbt_manifest, dbt_catalog, prompt,
                        additional_context, use_database):
        additional_context = f'REFERENCE LIBRARY: When encountering unfamiliar terminology, consult this supplementary knowledge base. The text below contains definitions, explanations, and contextual information for specialized terms, acronyms, and domain-specific language that may not be in standard training data. Use these values to explain acronyms and provide additional context to the user, incorporating explanations in your output: {additional_context}'
        return DbtToEnglish(dbt_manifest=dbt_manifest,
                            dbt_catalog=dbt_catalog,
                            node_id=node,
                            prompt=prompt,
                            additional_context=additional_context,
                            use_database=use_database)\
            .get_model_explanation()

    @staticmethod
    def get_dict_type_for_manifest(type_name):
        dict_type = 'nodes'
        if type_name == 'source':
            dict_type = 'sources'
        return dict_type

    @staticmethod
    def parse_artifacts_dict(artifacts_dict):
        parsed_dict = {
            'database': artifacts_dict.get('database'),
            'schema': artifacts_dict.get('schema'),
            'model_name': artifacts_dict.get('name'),
            'resource_type': artifacts_dict.get('resource_type'),
            'alias': artifacts_dict.get('alias'),
            'meta': artifacts_dict.get('config', {}).get('meta'),
            'materialized': artifacts_dict.get('config', {})
            .get('materialized'),
            'grants': artifacts_dict.get('config', {}).get('grants'),
            'description': artifacts_dict.get('description', {}),
            'raw_code': artifacts_dict.get('raw_code', {}),
            'depends_on': artifacts_dict.get('depends_on', {}),
            'columns': artifacts_dict.get('catalog_dict', {}).get('columns'),
            'rows_number': artifacts_dict.get('catalog_dict', {}).get('stats',
                                                                      {})
            .get('rows', {}).get('value')
        }
        return parsed_dict

    def get_model_explanation_from_llm(self, metadata_list):
        for token, metadata in self.react_agent.stream(
            {'messages': [('human', f"""Tell me about {self.node_id} model.
                                    {metadata_list}""")]},
                stream_mode='messages'):
            if len(self.llm_tools) == 0:
                yield token.content
            else:
                for chunk in token.content:
                    if type(chunk) is dict and chunk.get('type') == 'text':
                        yield chunk['text']
        # for token in self.react_agent.stream({'messages': [('human',
        #                               f"""Tell me about {self.node_id} model.
        #                             {metadata_list}""")]},
        #                                      stream_mode='values'):
        #     token["messages"][-1].pretty_print()
        #     yield 'l'

    def get_dbt_manifest_list(self):
        metadata_list = []

        def get_dependencies(node_id, level=1):
            type_name = node_id.split('.')[0]
            dict_type = DbtToEnglish.get_dict_type_for_manifest(type_name)
            main_dict = self.dbt_manifest[dict_type].get(node_id, None)
            if not main_dict:
                return
            main_dict['catalog_dict'] = self.dbt_catalog[dict_type]\
                .get(node_id, {})
            if level <= self.max_level or type_name == 'source':
                if level > 1:
                    # main_dict['raw_code'] = None
                    main_dict['catalog_dict'] = {}
                metadata_list.append(DbtToEnglish.parse_artifacts_dict(
                    main_dict))
            for dep in main_dict.get('depends_on', {}).get('nodes', []):
                get_dependencies(dep, level+1)
        get_dependencies(self.node_id)
        return metadata_list

    def get_model_explanation(self):
        metadata_list = self.get_dbt_manifest_list()
        return self.get_model_explanation_from_llm(metadata_list)

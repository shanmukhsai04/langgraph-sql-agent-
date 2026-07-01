# ![image.png](attachment:image.png)

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

import os
import re
import operator

from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model = "gpt-4o-mini")

# # Database setup
# - A database URI (Uniform Resource Identifier) is a formatted connection string that provides all the necessary information to connect to a specific database. It typically includes details such as the database engine, user credentials, host address, and database name, allowing applications to establish a connection

db = SQLDatabase.from_uri("sqlite:///sqllite/employees_db-full-1.0.6.db")

tables = db.get_usable_table_names()

print(tables)

SCHEMA = db.get_table_info()

print(SCHEMA)

# ## Tools Creation

@tool
def get_database_schema(table_name: str = None):
    """
    Get database schema information for SQL query generation.
    Use this first to understand table structure before creating queries
    """
    
    if table_name:
        tables = db.get_usable_table_names()
        if table_name.lower() in [t.lower() for t in tables]:
            result = db.get_table_info([table_name])
            return result
        
        else:
            return f"Error: Table '{table_name}' not found. Available tables: '{', '.join(tables)}'"
        
    else:
        return SCHEMA
            
        

#[t.lower() for t in tables]

result = get_database_schema.invoke("employees")
print(result)

result = get_database_schema.invoke("nitin")
print(result)

# ### Generating SQL Query

@tool
def generate_sql_query(question:str, schema_info: str=None):
    """
       Generate a SQL Select query from a natural language question using database schema.
       Always use this after getting schema information
    """
    
    
    schema_to_use = schema_info if schema_info else SCHEMA
    
    prompt = f"""Based on this database schema:
                {schema_to_use}

                Generate a SQL query to answer this question: {question}

                Rules:
                - Use only SELECT statements
                - Include only existing columns and tables
                - Add appropriate WHERE, GROUP BY, ORDER BY clauses as needed
                - Limit results to 10 rows unless specified otherwise
                - Use proper SQL syntax for SQLite

                Return only the SQL query, nothing else."""
                
                
    response = llm.invoke(prompt)
    sql_query = response.content.strip()
    
    print(f"[TOOL] Generated SQL Query: {sql_query}")
    
    return sql_query
                
                

generate_sql_query.invoke("How many employees are there?")

# 'SELECT COUNT(*) FROM employees;'


# Some times LLM generates query in markdown format
# ```sql
# 'SELECT COUNT(*) FROM employees;'
# ```

# ## Validating Query

@tool
def validate_sql_query(query: str):
    """
    Validate SQL query for safety and syntax before execution.
    Returns 'Valid: <query>' if safe or 'Error:<message>' if unsafe.
    """
    
    clean_query = query.strip()
    
    # Clean SQL Block
    # remove sql & `tilda` from the query
    clean_query = re.sub(r'```sql\s*', '', clean_query, flags=re.IGNORECASE) # this will remove '''sql and s* will remove all the spaces
    clean_query = re.sub(r'```\s*','', clean_query, flags=re.IGNORECASE) # This will remove ``` and s\* will remove all spaces`
    
    clean_query = clean_query.strip().rstrip(";")
    
    # Validating against manipulating dabase block
    if not clean_query.lower().startswith("select"):
        return "Error: only Select statements are allowed"
    
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP', 'CREATE', 'TRUNCATE']
    
    query_upper = clean_query.upper()
    
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return f"Error: {keyword} operation are not allowed"
    print("[TOOL] your sql query is validated. Passed!")
    
    return clean_query
    

'SELECT' in 'SELECT * FROM EMPLOYEES'

validate_sql_query.invoke("SELECT count(*) FROM employees")

validate_sql_query.invoke("TRUNCATE employees")

# ### Executing Query

@tool
def execute_sql_query(sql_query: str):
    """
    Execute a validated SQL query and return the results.
    Only use this after validating the query for safety
    """
    
    query = validate_sql_query.invoke(sql_query)
    
    if query.startswith("Error:"):
        return f"Query {sql_query} validation failed with error {query}"
    
    result = db.run(query)
    
    if result:
        return f"Query Results:{result}"
    else:
        return f"Query Executed Successfully bu no results found"

db.run("select count(*) from employees")

execute_sql_query.invoke("SELECT count(*) from employees")

execute_sql_query.invoke("TRUNCATE employees")

# ### Fixing SQL Errors

@tool
def fix_sql_error(original_query:str, error_message:str, question:str):
    """
    Fix a failed SQL query by analyzing the error and generating a corrected version.
    Use this when validation or execution fails
    """
    
    fix_prompt = f"""The following SQL query failed:
                    Query: {original_query}
                    Error: {error_message}
                    Original Question: {question}

                    Database Schema:
                    {SCHEMA}

                    Analyze the error and provide a corrected SQL query that:
                    1. Fixes the specific error mentioned
                    2. Still answers the original question
                    3. Uses only valid table and column names from the schema
                    4. Follows SQLite syntax rules

                    Return only the corrected SQL query, nothing else."""
                    
    
    response = llm.invoke(fix_prompt)
    
    query = response.content.strip()
    
    print(f"[TOOL] Generated fixed SQL Query")
    
    return query
    

# SQLite Agent Creation

# Creating AgentState
class AgentState(TypedDict):
    messages:Annotated[list, operator.add]
    
tools = [get_database_schema, generate_sql_query, execute_sql_query, fix_sql_error]    

tools

llm_with_tools = llm.bind_tools(tools)

print(llm_with_tools)

# ### SQLite Agent Node

def agent_node(state: AgentState):
    
    system_prompt = f"""You are an expert SQL analyst working with an employees database.

                    Database Schema:
                    {SCHEMA}

                    Your workflow for answering questions:
                    1. Use `get_database_schema` first to understand available tables and columns (if needed)
                    2. Use `generate_sql_query` to create SQL based on the question
                    3. Use `execute_sql_query` to run the validated query
                    4. If there's an error, use `fix_sql_error` to correct it and try again (up to 3 times)

                    Rules:
                    - Always follow the workflow step by step
                    - If a query fails, use the fix tool and try again
                    - Provide clear, informative answers
                    - Be precise with table and column names
                    - Handle errors gracefully and try to fix them
                    - If you fail after 3 attempts, explain what went wrong

                    Available tools:
                    - get_database_schema: Get table structure info
                    - generate_sql_query: Create SQL from question
                    - execute_sql_query: Run the query
                    - fix_sql_error: Fix failed queries

                    Remember: Always validate queries before executing them for safety."""
                    
    messages = [SystemMessage(system_prompt)] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    
    return {"messages":[response]}
    

llm_with_tools.invoke("How many emplyees are there?")

# AIMessage(content='', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 16, 'prompt_tokens': 205, 'total_tokens': 221, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'gpt-4o-mini-2024-07-18', 'system_fingerprint': 'fp_791df6ace0', 'id': 'chatcmpl-DgNZNL1RpK5W4VNWHgJSPrc4zb1LT', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019e343b-0a67-7fa1-89ee-6c261d4c7a8a-0', tool_calls=[{'name': 'get_database_schema', 'args': {'table_name': 'employees'}, 'id': 'call_0vxgOyjRrxhxnhxGWgdmuOxk', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 205, 'output_tokens': 16, 'total_tokens': 221, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}})

# ### Rounting Logic

def should_continue(state:AgentState):
    
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print("[TOOL] Calling the tool")
        for tc in last_message.tool_calls:
            print(f"Callling tool: '{tc['name']}' with Args: '{tc['args']}'")
            
        return "tools"
    else:
        print("[AGENT] Agent is procesing the query...")
        return END
    
    

# ### Building the Graph
#
#

def create_sql_agent():
    builder = StateGraph(AgentState)
    
    # Add Nodes
    builder.add_node("agent",agent_node)
    builder.add_node("tools",ToolNode(tools))
    
    # Add Edges
    builder.add_edge(START, "agent")
    builder.add_edge("tools","agent")
    
    # Routing or conditional edge
    builder.add_conditional_edges("agent",should_continue,["tools",END])
    
    graph = builder.compile()
    
    return graph
    

agent = create_sql_agent()
agent

query = "How many emplyees are there"

result = agent.invoke({"messages":[query]})

print(result)

result["messages"][-1].pretty_print()

query = "What is the average salary of employees in each department. show me fot the top 5 departments?"
result = agent.invoke({'messages': [query]})
result['messages'][-1].pretty_print()

query = "Show me the top 5 highest paid employees with their title and salaries?"
result = agent.invoke({'messages': [query]})
result['messages'][-1].pretty_print()

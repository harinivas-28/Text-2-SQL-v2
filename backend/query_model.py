from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import sys
import json
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os


# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("juierror/flan-t5-text2sql-with-schema-v2")
model = AutoModelForSeq2SeqLM.from_pretrained("juierror/flan-t5-text2sql-with-schema-v2")

# Define prompt creation function
def get_prompt(tables, question):
    prompt = f"""
You are a SQL query generator. Given the table structure and a question, generate a MySQL query that best answers the question.

Table Structure:
{tables}

Question:
{question}

Return the SQL query only:
"""
    return prompt

# Prepare input function
def prepare_input(question: str, tables: Dict[str, List[str]]):
    tables = [f"""{table_name}({",".join(tables[table_name])})""" for table_name in tables]
    tables = ", ".join(tables)
    prompt = get_prompt(tables, question)
    input_ids = tokenizer(prompt, max_length=512, truncation=True, return_tensors="pt").input_ids
    return input_ids

# Inference function
def inference(question: str, tables: Dict[str, List[str]]) -> str:
    input_data = prepare_input(question=question, tables=tables)
    input_data = input_data.to(model.device)
    outputs = model.generate(inputs=input_data, num_beams=5, max_length=128)  
    result = tokenizer.decode(token_ids=outputs[0], skip_special_tokens=True)
    result = post_process(result)
    return result

# Post-process function to clean up repetitive SQL query
def post_process(query: str) -> str:
    lines = query.split('\n')
    unique_lines = []
    for line in lines:
        if line not in unique_lines:
            unique_lines.append(line)
    return ' '.join(unique_lines)

table_name = 'data'

def replace_table_name(query, table_name):
    keywords = ["FROM", "JOIN"]
    revised_query = query

    for keyword in keywords:
        # Find the position of the keyword (FROM or JOIN)
        keyword_pos = revised_query.upper().find(keyword)
        while keyword_pos != -1:
            # Find the start and end position of the table name following the keyword
            start_pos = keyword_pos + len(keyword) + 1
            end_pos = start_pos
            while end_pos < len(revised_query) and revised_query[end_pos] != ' ':
                end_pos += 1

            # Extract the part before and after the table name
            before_table = revised_query[:start_pos]
            after_table = revised_query[end_pos:]

            # Create the revised query
            revised_query = before_table + table_name + after_table

            # Find the next occurrence of the keyword
            keyword_pos = revised_query.upper().find(keyword, keyword_pos + len(keyword))

    return revised_query

# Plotting function
def plot_result(result: pd.DataFrame, output_dir: str):
    if result.empty:
        print("Result DataFrame is empty.")
        return []

    plot_paths = []
    num_columns = len(result.columns)
    
    # Single Column: Histogram or Pie Chart
    if num_columns == 1:
        column = result.columns[0]
        if pd.api.types.is_numeric_dtype(result[column]):
            plt.figure()
            sns.histplot(result[column], kde=True)
            plt.xlabel(column)
            plt.title(f'Distribution of {column}')
            plot_path = os.path.join(output_dir, f'_histogram.png')
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()
        else:
            if result[column].dtype == 'object':
                value_counts = result[column].value_counts()
                plt.figure()
                plt.pie(value_counts, labels=value_counts.index, autopct='%1.1f%%')
                plt.title(f'Distribution of {column}')
                plot_path = os.path.join(output_dir, f'_piechart.png')
                plt.savefig(plot_path)
                plot_paths.append(plot_path)
                plt.close()
            else:
                print(f"Cannot plot pie chart for non-categorical data in column {column}")
    
    # Two Columns: Bar Plot, Scatter Plot, or Count Plot
    elif num_columns == 2:
        x_col, y_col = result.columns
        if pd.api.types.is_numeric_dtype(result[x_col]) and pd.api.types.is_numeric_dtype(result[y_col]):
            plt.figure()
            sns.scatterplot(x=x_col, y=y_col, data=result)
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f'{y_col} vs {x_col}')
            plot_path = os.path.join(output_dir, f'_scatter.png')
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()
        elif pd.api.types.is_numeric_dtype(result[y_col]) and result[x_col].dtype == 'object':
            plt.figure()
            sns.barplot(x=x_col, y=y_col, data=result)
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f'{y_col} by {x_col}')
            plot_path = os.path.join(output_dir, f'_bar.png')
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()
        elif result[x_col].dtype == 'object' and result[y_col].dtype == 'object':
            plt.figure()
            sns.countplot(x=x_col, hue=y_col, data=result)
            plt.xlabel(x_col)
            plt.title(f'{y_col} count by {x_col}')
            plot_path = os.path.join(output_dir, f'_count.png')
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()
    
    # More than Two Columns: Heatmap for Correlation or Pair Plot
    else:
        numeric_cols = result.select_dtypes(include='number').columns
        if len(numeric_cols) > 1:
            plt.figure()
            corr = result[numeric_cols].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
            plt.title('Correlation Heatmap')
            plot_path = os.path.join(output_dir, 'correlation_heatmap.png')
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()
        else:
            plt.figure()
            sns.pairplot(result)
            plt.title('Pair Plot')
            plot_path = os.path.join(output_dir, 'pair_plot.png')
            plt.savefig(plot_path)
            plot_paths.append(plot_path)
            plt.close()

    return plot_paths

def get_dataframe_head(csv_path: str, n: int = 5) -> pd.DataFrame:
    """
    Reads the CSV file and returns the first few rows of the DataFrame.

    Args:
    - csv_path (str): Path to the CSV file.
    - n (int): Number of rows to return (default is 5).

    Returns:
    - pd.DataFrame: DataFrame containing the first `n` rows.
    """
    df = pd.read_csv(csv_path)
    return df.head(n)


if __name__ == "__main__":
    try:
        # Get input data from command-line arguments
        input_data = sys.argv[1]
        try:
            input_data = json.loads(input_data)
        except json.JSONDecodeError as e:
            result_json = {"error": f"Invalid JSON input: {e}"}
            print(json.dumps(result_json, ensure_ascii=False, separators=(',', ':')))
            # sys.exit(1) 
        question = input_data["question"]
        tables = input_data["tables"]
        csv_path = input_data["csv_path"]

        # Load the CSV file into a DataFrame
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
        except FileNotFoundError as e:
            result_json = {"error": f"CSV file not found: {e}"}
            print(json.dumps(result_json, ensure_ascii=False, separators=(',', ':')))
            # sys.exit(1)

        # Create table structure from DataFrame
        table_name = 'data'
        table_structure = {table_name: df.columns.tolist()}

        # Get SQL query
        sql_query = inference(question=question, tables=table_structure)
        sql_query = sql_query.replace('table_name', table_name)

        # Replace the table name in the SQL query
        revised_sql_query = replace_table_name(sql_query, table_name)
        
        # Create an in-memory SQLite database
        conn = sqlite3.connect(':memory:')

        # Load DataFrame into SQLite
        df.to_sql(table_name, conn, index=False, if_exists='replace')

        # Execute the generated SQL query
        try:
            result = pd.read_sql_query(revised_sql_query, conn)
            output_dir = "output_plots"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            plot_paths = plot_result(result, output_dir)
            result_json = {
                "query": revised_sql_query,
                "result": result.to_dict(orient='records'),
                "plots": plot_paths
            }
            print(json.dumps(result_json, ensure_ascii=False, separators=(',', ':')))
        except Exception as e:
            result_json = {
                "query": revised_sql_query,
                "error": f"Error executing SQL query: {e}" 
            }
            print(json.dumps(result_json, ensure_ascii=False, separators=(',', ':')))
            # sys.exit(1) 
    except Exception as e:
        result_json = {"error": str(e)}
        print(json.dumps(result_json, ensure_ascii=False, separators=(',', ':')))

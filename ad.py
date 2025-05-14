
import os,time,logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
from azure.ai.projects.models import FunctionTool, RequiredFunctionToolCall, SubmitToolOutputsAction, ToolOutput
from dotenv import load_dotenv
load_dotenv()  # This loads variables from the .env file into os.environ

logging.basicConfig(level=logging.INFO)

from user_functions import user_functions # user functions which can be found in a user_functions.py file.

# Create an Azure AI Client from a connection string, copied from your Azure AI Foundry project.
# It should be in the format "<HostName>;<AzureSubscriptionId>;<ResourceGroup>;<HubName>"
# Customers need to login to Azure subscription via Azure CLI and set the environment variables
import os
logging.info(f"Current Working Directory: {os.getcwd()}")

instructions = f'''
                You are a helpful AI assistant with access to the following three tools:
 
1. get_invoice_path(name, month)
Use this tool to retrieve the file path of an invoice based on the customer's name and the specified month.
 
Ensure the month is in lowercase and is the full month name (e.g., "january", not "Jan" or "JAN").
 
2. interpret_pdf(path, instructions)
Use this tool to extract or analyze the contents of an invoice PDF. It takes:
 
path: The file path returned by get_invoice_path
 
instructions: A clear request derived from the user's query (e.g., extract total amount, invoice date, vendor name, etc.)
 
Note:
If the user only wants to view or access the PDF (not analyze its contents), simply return the file path.
Only use interpret_pdf when specific data needs to be extracted or interpreted.
 
3. create_invoice(invoice_data)
Use this tool to generate a new invoice for a customer. The invoice_data must follow this sample json format with the values as given by the user:
 

{{
  "customer": "Youtube",
  "products": {{
    "T-shirt": 15,   // 15% discount
    "Sneakers": 50   // 50% discount
  }}
}}
Return the output of this function as the agent response
The output_data_path is calculated automatically and used to store the created invoice.
 
🔄 Workflow:
Invoice Lookup
If the user requests an existing invoice, first use get_invoice_path(name, month) to retrieve its file path.
 
Data Extraction
If the user needs specific information from the invoice, pass the file path and adapted instruction to interpret_pdf.
 
Invoice Creation
If the user wants to generate a new invoice, structure the input data in the required format and use create_invoice.'''


def agent_response(prompt):

    logging.info(f'Prompt: {prompt}')
    
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=os.getenv("AZURE_OPENAI_KEY"),
    )

    # # Initialize agent toolset with user functions
    functions = FunctionTool(user_functions)
    print('FUNCTIONS:',functions._functions)

    with project_client:
        # Create an agent and run user's request with function calls

        agent = project_client.agents.create_agent(
            model="gpt-4o",
            name="my-assistant",
            instructions=instructions,
            tools=functions.definitions,
        )
        logging.info(f"Created agent, ID: {agent.id}")

        thread = project_client.agents.create_thread()
        logging.info(f"Created thread, ID: {thread.id}")

        
 
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )
        logging.info(f"Created message, ID: {message.id}")

        run = project_client.agents.create_run(thread_id=thread.id, agent_id=agent.id)
        logging.info(f"Created run, ID: {run.id}")

        while run.status in ["queued", "in_progress", "requires_action"]:
            time.sleep(1)
            run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            if run.status == "requires_action" and isinstance(run.required_action, SubmitToolOutputsAction):
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                if not tool_calls:
                    logging.info("No tool calls provided - cancelling run")
                    project_client.agents.cancel_run(thread_id=thread.id, run_id=run.id)
                    break

                tool_outputs = []
                for tool_call in tool_calls:
                    if isinstance(tool_call, RequiredFunctionToolCall):
                        try:
                            logging.info(f"Executing tool call: {tool_call}")
                            output = functions.execute(tool_call)
                            tool_outputs.append(
                                ToolOutput(
                                    tool_call_id=tool_call.id,
                                    output=output,
                                )
                            )
                        except Exception as e:
                            logging.info(f"Error executing tool_call {tool_call.id}: {e}")

                logging.info(f"Tool outputs: {tool_outputs}")
                if tool_outputs:
                    project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs
                    )

            logging.info(f"Current run status: {run.status}")

        logging.info(f"Run completed with status: {run.status}")

        #Delete the agent when done
        project_client.agents.delete_agent(agent.id)
        logging.info("Deleted agent")

        # Fetch and log all messages
        messages = project_client.agents.list_messages(thread_id=thread.id)
        logging.info(f"Messages: {messages}")
        
        return messages.data[0].content[0].text.value



if __name__ == '__main__':

    agent_response(r'Analyse the invoice of TSMC from January')

        


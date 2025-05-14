import azure.functions as func
import datetime
import json
import logging
from ad import agent_response

app = func.FunctionApp()

@app.route(route="agent_call", auth_level=func.AuthLevel.ANONYMOUS)
def agent_call(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    input = req.params.get('input')
    if not input:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            input = req_body.get('input')

    if input:
        response = agent_response(input)
        return func.HttpResponse(f"Response: {response}")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
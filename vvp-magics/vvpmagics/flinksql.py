import json
from pandas import DataFrame

def sql_execute_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:execute".format(namespace)


def sql_validate_endpoint(namespace):
    return "/sql/v1beta1/namespaces/{}/sqlscripts:validate".format(namespace)


sql_validate_supported_responses = [
    "VALIDATION_RESULT_VALID_DDL_STATEMENT",
    "VALIDATION_RESULT_VALID_COMMAND_STATEMENT"
]
sql_validate_possible_responses = \
    sql_validate_supported_responses + [
        "VALIDATION_RESULT_INVALID",
        "VALIDATION_RESULT_INVALID_QUERY",
        "VALIDATION_RESULT_UNSUPPORTED_QUERY",
        "VALIDATION_RESULT_VALID_INSERT_QUERY",
        "VALIDATION_RESULT_VALID_SELECT_QUERY"
    ]


def is_invalid_request(response):
    return response.status_code != 200 \
           or json.loads(response.text)['validationResult'] not in sql_validate_possible_responses


def is_supported_sql_command(response):
    return json.loads(response.text)['validationResult'] in sql_validate_supported_responses


def run_query(session, cell):
    validation_response = _validate_sql(cell, session)
    if is_invalid_request(validation_response):
        raise FlinkSqlRequestException("Bad HTTP request or incompatible VVP back-end.", sql=cell)
    if is_supported_sql_command(validation_response):
        execute_command_response = _execute_sql(cell, session)
        json_data = json.loads(execute_command_response.text)
        return _json_convert_to_dataframe(json_data)
    else:
        raise SqlSyntaxException("Invalid or unsupported SQL statement.", sql=cell, response=validation_response)


def _validate_sql(cell, session):
    validate_endpoint = sql_validate_endpoint(session.get_namespace())
    body = json.dumps({"script": cell})
    validation_response = session.submit_post_request(validate_endpoint, body)
    return validation_response


def _json_convert_to_dataframe(json_data):
    if "resultTable" not in json_data:
        return json_data

    table = json_data["resultTable"]
    headers = table["headers"]
    rows = table["rows"]
    columns = []
    for h in headers:
        for v in h.values():
            columns.append(v)

    data = []
    for row in rows:
        cells = row["cells"]
        cellData = []
        for cell in cells:
            for cellValue in cell.values():
                cellData.append(cellValue)
        data.append(cellData)

    return DataFrame(data=data, columns=columns)

def _execute_sql(cell, session):
    execute_endpoint = sql_execute_endpoint(session.get_namespace())
    body = json.dumps({"statement": cell})
    execute_response = session.submit_post_request(execute_endpoint, body)
    return execute_response


class SqlSyntaxException(Exception):

    def __init__(self, message="", sql=None, response=None):
        self.message = message
        self.sql = sql
        self.details = json.loads((response and response.text) or "{}")

    def get_details(self):
        return self.details


class FlinkSqlRequestException(Exception):

    def __init__(self, message="", sql=None):
        self.message = message
        self.sql = sql

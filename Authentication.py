import urllib.parse
import requests
import os
import msal
from msal import SerializableTokenCache, PublicClientApplication

import urllib

from dotenv import load_dotenv, find_dotenv
load_dotenv()

class Authentication:
    
    def __init__(self) -> None:
        self.tenant_id: str = os.getenv('AZURE_TENANT_ID')
        self.client_id: str = os.getenv('AZURE_CLIENT_ID')
        self.client_secret: str = os.getenv('AZURE_CLIENT_SECRET_NEW')
        # self.resource: str = os.getenv('RESOURCE')
        self.resource: str = os.getenv('SANDBOX_RESOURCE')
        self.token_cache_file: str = os.getenv('TOKEN_CACHE_FILE')
        self.dataverse_api_url: str = os.getenv('MAIN_DATAVERSE_API_URL')
        # self.choice_column_value: str = os.getenv('CHOICE_VALUE')
        self.authenticate_session()

    def load_token_cache_file(self) -> None:
        self.token_cache: SerializableTokenCache = msal.SerializableTokenCache()
        if os.path.exists(self.token_cache_file):
            self.token_cache.deserialize(open(self.token_cache_file, 'r').read())
        else:
            env_file_path = find_dotenv()
            token_cache_file_path = f"{env_file_path[:env_file_path.rfind('\\') + 1]}{self.token_cache_file}"
            self.token_cache_file = token_cache_file_path
            if os.path.exists(self.token_cache_file):
                self.token_cache.deserialize(open(self.token_cache_file, 'r').read())

    def get_bearer_token(self) -> str:
        self.load_token_cache_file()
        authority_url = f'https://login.microsoftonline.com/{self.tenant_id}'

        app: PublicClientApplication = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=authority_url,
            token_cache=self.token_cache
        )

        # Default scope for msal authentication
        scopes = [f'{self.resource}/.default']

        # Tries to get authenticated account using the cached token
        # If no cached token, this would return None
        accounts = app.get_accounts()
        if accounts:
            auth_result = app.acquire_token_silent(scopes, account=accounts[0])
        else:
            flow = app.initiate_device_flow(scopes=scopes)

            # Might need to change later
            print('Go to', flow['verification_uri'])
            print('Enter code:', flow['user_code'])

            auth_result = app.acquire_token_by_device_flow(flow)

        # Token will always change anytime a proper connection was made
        if self.token_cache.has_state_changed:
            with open(self.token_cache_file, 'w') as f:
                f.write(self.token_cache.serialize())

        if 'access_token' in auth_result:
            return auth_result['access_token']

    def authenticate_session(self) -> None:
        print('Auth session')
        self.session = requests.Session()
        headers = {
            'Authorization': f'Bearer {self.get_bearer_token()}',
            'Content-Type': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json'
        }

        self.session.headers.update(headers)

    def test_connection(self) -> int:
        # a test request to the URI
        query_options = {
            'top': 1,
            'select': 'internalemailaddress'
        }

        r = self.get_table_from_dataverse('systemusers', query_parameters=query_options)

        response = ''

        if r.status_code != 200:
            print('Request failed. Error code: ')
            raw = r.content.decode('utf-8')
            response = raw

        else:
            response = 'Connection successful'
        
        print(response)

        return r.status_code
    
    def _get_request_url(self, tablename):
        return f'{self.resource}{self.dataverse_api_url}{tablename}'

    def post_to_table_in_dataverse(self, tablename, json_parameters) -> requests.Response:

        # Validate json (Maybe)

        request_url = self._get_request_url(tablename)
        response = self.session.post(request_url, json=json_parameters)
        return response

    def get_table_from_dataverse(self, tablename, query_parameters=None) -> requests.Response | None:
        # query_parameters is used for any filter or selection
        query_functions = ''
        
        if query_parameters:
            query_options = {'select': self._select_option, 'expand': self._expand_option, 'orderby': self._orderby_option, 
                             'filter': self._filter_option, 'apply': self._apply_option, 'top': self._top_option, 'count': self._count_option}
            query_keys = query_parameters.keys()
            for key in query_keys:
                if isinstance(key, str):
                    key = key.lower()
                if key not in query_options:
                    return None # Logging here later (Maybe)

                if query_functions == '':
                    query_functions = f'?${key}={query_options[key](query_parameters[key])}'
                else:
                    query_functions = f'{query_functions}&${key}={query_options[key](query_parameters[key])}'

        request_url = f'{self._get_request_url(tablename)}{query_functions}'
        # print(request_url)
        return self._get_from_dataverse(request_url)
    
    def _get_from_dataverse(self, request_url) -> requests.Response:
        # print(request_url)
        return self.session.get(request_url)

    def _select_option(self, *args) -> str:
        return_string = ''
        # args = (['column1', 'column2'],)
        for item in args:
            if isinstance(item, list):
                for subitem in item:
                    if return_string == '':
                        return_string = str(subitem)
                    else:
                        return_string += f',{str(subitem)}'
            else:
                if return_string == '':
                    return_string = str(item)
                else:
                    return_string += f',{str(item)}'
        print(return_string)
        return return_string

    def _filter_option(self, *args) -> str:
        # TODO

        # Check for proper filter format

        # args = ({'and': {'column1': 'value1', 'column2': 'value2'}},)
        arg_item = args[0]
        arg_item_key = list(arg_item.keys())[0]

        # AND and OR option only, maybe add a NOT option later
        # AND will be the default
        if arg_item_key != 'not' and arg_item_key != 'or':
            filter_type = 'and'
        else:
            filter_type = arg_item_key
            
        filter_conditions = []

        for k, v in arg_item[arg_item_key].items():
            if type(v) is not list:
                filter_conditions.append(f"{k} eq {self._quote_only_strings(v)}")
                continue

            for value in v:
                filter_conditions.append(f'{k} eq {self._quote_only_strings(value)}')


        # filter_conditions = [f'{k} eq {self._quote_only_strings(v)}' for k, v in arg_item[arg_item_key].items()]
        odata_filter = f' {filter_type} '.join(filter_conditions)
        encoded_filter = urllib.parse.quote(odata_filter)

        return encoded_filter

    def _quote_only_strings(self, value) -> str:
        if isinstance(value, str):
            return f'{value}'
        return str(value)

    def _expand_option(self, *args) -> str:
        # TODO
        pass

    def _orderby_option(self, *args) -> str:
        # TODO
        pass

    def _apply_option(self, *args) -> str:
        # TODO
        pass

    def _top_option(self, *args) -> int:
        return args[0] # Only a number

    def _count_option(self, *args) -> str:
        # TODO
        pass

    def patch_row_in_dataverse(self, tablename, json_parameter, GUID) -> requests.Response:
        # TODO
        
        # Validate json (Maybe)

        request_url = f'{self._get_request_url(tablename)}({GUID})'
        # print(request_url, ' : ', json_parameter)
        return self.session.patch(request_url, json=json_parameter)

    def get_choice_from_dataverse(self, choice_name) -> requests.Response:
        request_url = f"{self._get_request_url('GlobalOptionSetDefinitions')}(Name='{choice_name}')"
        return self._get_from_dataverse(request_url)

    def delete_row_in_dataverse(self, tablename, GUID) -> requests.Response:
        request_url = f'{self._get_request_url(tablename)}({GUID})'
        return self.session.delete(request_url)

    def upload_file_to_dataverse(self, tablename, file_data, file_name, GUID, column_name) -> requests.Response:
        r"""Uploads a file to the dataverse using PATCH request. Returns :class:`Response` object.

        :param tablename: Name of the table in the Dataverse which will receive the file object.
        :param file_data: Bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param file_name: Name that will show in the Dataverse column when viewed.
        :param GUID: Record ID inside the Dataverse.
        :param column_name: Name of the column which will receive the file object.
        :rtype: requests.Response
        """
        # Different headers for file upload
        # This will not affect the default headers given during object creation
        # Using the headers=headers parameter option will create a new Request using the given headers, the default headers when session was creating stick as default
        # Any headers given as a parameter will be used, only defaulting when no headers are given
        headers = {
            'Authorization': f'Bearer {self.get_bearer_token()}',
            'Content-Type': 'application/octet-stream',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json',
            'x-ms-file-name': file_name
        }

        # Patch function so record already has to exist
        upload_url = f"{self._get_request_url(tablename)}({GUID})/{column_name}"
        return self.session.patch(upload_url, headers=headers, data=file_data)

# Status code 401 session expired

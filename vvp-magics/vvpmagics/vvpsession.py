import json

from .httpsession import HttpSession

namespaces_endpoint = "/namespaces/v1/namespaces"


class VvpSession:
    sessions = {}
    default_session = None

    def __init__(self, vvp_base_url: str, namespace: str):
        """

        :type http_session: HttpSession
        :type namespace: string
        :type vvp_base_url: string
        """

        self._http_session = HttpSession(vvp_base_url, None)

        if not self._is_valid_namespace(namespace):
            raise Exception("Invalid or empty namespace specified.")
        self._namespace = namespace

    @staticmethod
    def get_sessions():
        return VvpSession.sessions.keys()

    @classmethod
    def create_session(cls, vvp_base_url, namespace, session_name, set_default=False, force=False):
        session = cls(vvp_base_url, namespace)
        cls._add_session_to_dict(session_name, session, force=force)
        if (cls.default_session is None) or set_default:
            cls.default_session = session
        return session

    @classmethod
    def _add_session_to_dict(cls, session_name, session, force=False):
        if (session_name in cls.sessions) and not force:
            raise Exception("The session name already exists. Please use --force to update.")
        cls.sessions[session_name] = session

    def get_namespace(self):
        return self._namespace

    def get_namespace_info(self):
        return self._get_namespace(self._namespace)

    def _is_valid_namespace(self, namespace):
        if not namespace:
            return False

        request = self._http_session.get(namespaces_endpoint + "/{}".format(namespace))
        validity_from_statuscodes = {200: True, 404: False}
        return validity_from_statuscodes[request.status_code]

    def _get_namespace(self, namespace):
        request = self._http_session.get(namespaces_endpoint + "/{}".format(namespace))
        namespace = (json.loads(request.text))["namespace"]
        return namespace

    def submit_post_request(self, endpoint, requestbody):
        request = self._http_session.post(
            path=endpoint,
            request_headers={"Content-Type": "text/plain"},
            data=requestbody
        )
        return request

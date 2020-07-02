from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic)
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring
from IPython import get_ipython
import sys

from vvpmagics.flinksql import run_query, SqlSyntaxException
from vvpmagics.vvpsession import VvpSession

from pandas import DataFrame

print('Loading vvp-vvpmagics.')


def connect_completers(self, event):
    return ['--port', '--namespace', '--session', '--force', '--debug']


def flink_sql_completers(self, event):
    return ['--session', '--force', '--debug']


@magics_class
class VvpMagics(Magics):

    def __init__(self, shell=None):
        super(VvpMagics, self).__init__(shell)
        self._ipython_shell = get_ipython()
        if self._ipython_shell is not None:
            self._ipython_shell.set_hook('complete_command', connect_completers, str_key='%connect_vvp')
            self._ipython_shell.set_hook('complete_command', flink_sql_completers, re_key='%%flink_sql')

    @line_magic
    @magic_arguments()
    @argument('hostname', type=str, help='Hostname')
    @argument('-p', '--port', type=str, default="8080", help='Port')
    @argument('-n', '--namespace', type=str, help='Namespace. If empty, lists all namespaces.')
    @argument('-s', '--session', type=str, help='Session name')
    @argument('-f', '--force', type=bool, help='Force updating of session names.')
    @argument('-d', '--debug', type=bool, default=False, nargs="?", const=True, help='Print traceback for all exceptions for debugging.')
    def connect_vvp(self, line):
        args = parse_argstring(self.connect_vvp, line)
        hostname = args.hostname
        port = args.port
        vvp_base_url = "http://{}:{}".format(hostname, port)
        try:
            if args.namespace:
                session_name = args.session or VvpSession.default_session_name
                force_update = args.force or False
                if session_name is None:
                    self.print_error("No session name given and none already exist.")
                else:
                    return VvpSession.create_session(vvp_base_url, args.namespace, session_name, force=force_update)
            else:
                return VvpSession.get_namespaces(vvp_base_url)
        except Exception as exception:
            self.print_error(exception)
            if args.debug or False:
                raise exception

    @cell_magic
    @magic_arguments()
    @argument('-s', '--session', type=str, help='Name of the object representing the connection '
                                                'to a given vvp namespace.')
    @argument('-o', '--output', type=str, help='Name of variable to assign the resulting data frame to. '
                                               'Nothing will be assigned if query does not result in data frame')
    @argument('-d', '--debug', type=bool, default=False, nargs="?", const=True, help='Print traceback for all exceptions for debugging.')
    def flink_sql(self, line, cell):
        args = parse_argstring(self.flink_sql, line)

        if cell:
            try:
                session = VvpSession.get_session(args.session)
                result = run_query(session, cell)
                if (args.output is not None) and (isinstance(result, DataFrame)):
                    self.shell.user_ns[args.output] = result
                return result
            except Exception as exception:
                if hasattr(exception, 'message'):
                    self.print_error(exception.message)
                else:
                    self.print_error(exception)
                if args.debug or False:
                    if hasattr(exception, 'get_details'):
                        self.print_error(exception.get_details())
                    raise exception

        else:
            print("Empty cell: doing nothing.")

    def print_error(self, error_message):
        self._ipython_shell.write_err(u"{}\n".format(error_message))
        sys.stderr.flush()

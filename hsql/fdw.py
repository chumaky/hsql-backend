"""Foreign server management"""
import psycopg2

from .config import ConfigParser
from .connection import Connection

class FDW:
    """Foreign server management"""

    def __init__(self, config_file: str = None):
        self.config = ConfigParser(config_file).params
        self.conn = Connection()

    @property
    def servers(self):
        """List of foreign servers"""
        #print(self.config)
        return self.config['servers'] if 'servers' in self.config else {}


    def init_servers(self):
        """Get list of enabled extensions"""
        try:
            cur = self.conn.cursor

            for server, props in self.servers.items():
                #print(f'{server} - {props}')
                options = ', '.join([f"{option} '{value}'" for option, value in props['options'].items()])
                sql = \
                    f'CREATE SERVER IF NOT EXISTS {server} ' \
                    f"FOREIGN DATA WRAPPER {props['fdw_name']} " \
                    f'OPTIONS ({options})'

                print(sql)
                cur.execute(sql)
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f'Error code: {e.pgcode}, Message: {e.pgerror}' f'SQL: {sql}')
        finally:
            cur.close()


    def create_user_mappings(self):
        """Create user mapping for a foreign servers"""
        try:
            cur = self.conn.cursor

            for server, props in self.servers.items():
                #print(f'{server} - {props}')
                options = ', '.join([f"{option} '{value}'" for option, value in props['user_mapping'].items()])
                sql = \
                    f'CREATE USER MAPPING IF NOT EXISTS FOR CURRENT_USER ' \
                    f"SERVER {server} " \
                    f'OPTIONS ({options})'

                print(sql)
                cur.execute(sql)
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f'Error code: {e.pgcode}, Message: {e.pgerror}' f'SQL: {sql}')
        finally:
            cur.close()


    def import_foreign_schema(self):
        """Import foreign schema"""
        try:
            cur = self.conn.cursor

            for server, props in self.servers.items():
                #print(f'{server} - {props}')
                conf = props['import_foreign_schema']
                remote_schema = conf['remote_schema']
                local_schema = conf['local_schema']

                sql = f'DROP SCHEMA IF EXISTS {local_schema} CASCADE; ' f'CREATE SCHEMA IF NOT EXISTS {local_schema}'
                print(sql)
                cur.execute(sql)

                sql = \
                    f'IMPORT FOREIGN SCHEMA "{remote_schema}" ' \
                    f'FROM SERVER {server} ' \
                    f'INTO {local_schema} '

                if 'options' in conf:
                    options = ', '.join([f"{option} '{value}'" for option, value in conf['options'].items()])
                    sql += f'OPTIONS(${options})'

                print(sql)
                cur.execute(sql)
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f'Error code: {e.pgcode}, Message: {e.pgerror}' f'SQL: {sql}')
        finally:
            cur.close()

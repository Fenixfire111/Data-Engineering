import argparse
import json
import dicttoxml
import psycopg2
from psycopg2 import OperationalError
import configparser

"""create a parser for the config file"""
config = configparser.ConfigParser()
config.read("config.ini")

# database name
DB_NAME = config.get('Db', 'db_name')
# database user
DB_USER = config.get('Db', 'db_user')
# user password
DB_PASSWORD = config.get('Db', 'db_password')
# host
DB_HOST = config.get('Db', 'db_host')
# port
DB_PORT = config.get('Db', 'db_port')


def main() -> bool:
    # connect_to_db
    connection = create_connection()
    # get command line arguments
    args = get_args()
    # clear tables for new data
    clear_tables(connection)
    # load data
    load_input_data(args, connection)
    # get result data
    output_data = execute_selected_query(connection, args['query'])
    # add indexes (optional)
    add_indexes(connection, args['index'])
    # output result data to the file
    output_result(args['format'], output_data)

    return True


def create_connection() -> psycopg2.extensions.connection:
    """connect_to_db"""
    connection = None
    try:
        connection = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def execute_query(connection: psycopg2.extensions.connection, query: str) -> bool:
    """execute sql query"""
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    try:
        return cursor.fetchall()
    except psycopg2.ProgrammingError:
        return True


def get_args() -> dict:
    """create a parser to process command line arguments
    and get command line arguments"""
    arg_parser = argparse.ArgumentParser(
        description='The program executes the selected query and outputs the result to json/xml file')
    arg_parser.add_argument('--query', nargs=1,
                            type=int,
                            metavar='<query>',
                            default=1,
                            help='executes one of four queries')

    arg_parser.add_argument('--students', nargs=1,
                            type=str,
                            metavar='<students>',
                            default='data/students.json',
                            help='path to student file')

    arg_parser.add_argument('--rooms', nargs=1,
                            type=str,
                            metavar='<rooms>',
                            default='data/rooms.json',
                            help='path to room file')

    arg_parser.add_argument('--format', nargs=1,
                            type=str,
                            metavar='<format>',
                            default='json',
                            help='output format: xml or json')

    arg_parser.add_argument('--index', nargs=1,
                            type=bool,
                            metavar='<index>',
                            default=False,
                            help='add indexes')
    args_dict = {'query': arg_parser.parse_args().query, 'students': arg_parser.parse_args().students[0],
                 'rooms': arg_parser.parse_args().rooms[0], 'format': arg_parser.parse_args().format[0],
                 'index': arg_parser.parse_args().index}
    return args_dict


def load_data(connection: psycopg2.extensions.connection, file_name: str, table_name: str) -> bool:
    """load data from a file into a table"""
    insert_query = f"""INSERT INTO {table_name} 
                    SELECT * FROM json_populate_recordset(NULL::{table_name}, %s) """

    with open(file_name) as file:
        file_content = file.read()
        json_data = json.loads(file_content)

        connection.autocommit = True
        cursor = connection.cursor()
        try:
            cursor.execute(insert_query, (json.dumps(json_data),))
            print("Query executed successfully")
        except OperationalError as e:
            print(f"The error '{e}' occurred")

    return True


def clear_tables(connection: psycopg2.extensions.connection) -> bool:
    """clear data in tables"""
    sql = """DELETE FROM rooms;"""
    execute_query(connection, sql)
    sql = """DELETE FROM students;"""
    execute_query(connection, sql)
    return True


def load_input_data(args: dict, connection: dict) -> bool:
    """load data in tables (rooms and students)"""
    load_data(connection, args['rooms'], 'rooms')
    load_data(connection, args['students'], 'students')
    return True


def execute_selected_query(connection: psycopg2.extensions.connection, query: int) -> list:
    """execute the user's query"""
    if query == 1:
        sql_query = """SELECT rooms.name, COUNT(rooms.id) FROM rooms JOIN
             students ON rooms.id = students.room GROUP BY rooms.id; """
    elif query == 2:
        sql_query = """SELECT rooms.name, AVG(age(CURRENT_DATE, birthday)) AS avg_old FROM rooms 
     JOIN students ON rooms.id = students.room GROUP BY rooms.id ORDER BY avg_old LIMIT 5;"""
    elif query == 3:
        sql_query = """SELECT rooms.name, (MAX(students.birthday) - MIN(students.birthday)) AS diff_old  FROM rooms 
             JOIN students ON rooms.id = students.room GROUP BY rooms.id ORDER BY diff_old DESC LIMIT 5;"""
    else:
        sql_query = """SELECT rooms.id, rooms.name FROM rooms JOIN students ON rooms.id = students.room 
             GROUP BY rooms.id HAVING COUNT(DISTINCT(students.sex)) = 2;"""

    return execute_query(connection, sql_query)


def add_indexes(connection: psycopg2.extensions.connection, condition: bool) -> bool:
    """adds indexes (upon user decision)"""
    if condition:
        sql_query = """CREATE INDEX IF NOT EXISTS index_students ON students(room,birthday, sex);
            CREATE INDEX IF NOT EXISTS index_rooms ON rooms(id);"""
        return execute_query(connection, sql_query)
    else:
        return False


def delete_index(connection: psycopg2.extensions.connection) -> bool:
    """delete indexes"""
    sql_query = """DROP INDEX index_students;
       DROP INDEX index_rooms;"""
    return execute_query(connection, sql_query)


def output_result(file_format: str, data: list) -> bool:
    """output result data"""
    if file_format == 'json':
        with open('result.json', 'w') as f:
            dict_data = dict(data)
            final_data = json.dumps(dict_data, indent=4, default=str)
            f.write(final_data)
    else:
        dict_data = dict(data)
        final_data = dicttoxml.dicttoxml(data)
        with open('result.xml', 'wb') as f:
            f.write(final_data)
    return True


if __name__ == '__main__':
    main()

import os
import errno
import argparse    as ap
from   jinja2      import Environment, PackageLoader
from   collections import MutableSequence


def mkdirs(new_directory, mode=0755):
    """
    Wrapper around os.makedirs, that doesn't complain if directory exists.
    """
    try:
        os.makedirs(new_directory, mode)
    except OSError, e:
        # Reraise if it's not about directory existing
        if e.errno != errno.EEXIST or not os.path.isdir(new_directory):
            raise


JINJA_ENV      = Environment(loader        = PackageLoader('spill', 'templates'),
                             trim_blocks   = True,
                             lstrip_blocks = True)
SUPPORTED_DBS  = ['sqlite', 'mysql', 'mongo']
SUPPORTED_ORMS = ['sqlalchemy', 'mongoengine']


class Scaffold(object):
    """
    A base object with some common methods for generating boilerplate.
    """
    def __init__(self, directory, name=None):
        super(Scaffold, self).__init__()
        self.directory = directory
        self.name      = name if name else os.path.basename(directory)

    def __repr__(self):
        return "%s(name=%s)" % (self.__class__.__name__, self.name)

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, directory):
        if os.path.isfile(directory):
            raise OSError('A file with your project name already exists at this location')
        mkdirs(directory)
        self._directory = directory

    @directory.deleter
    def directory(self):
        del self._directory

    def _write_template(self, template_jnj, output_file, **variables):
        template = JINJA_ENV.get_template(template_jnj)
        output   = template.render(variables)
        with open(output_file, 'w') as f:
            f.write(output)

    def create(self):
        raise NotImplementedError


class Project(Scaffold):
    """
    A Flask project, composed of an app, a database, and tests.
    """
    def __init__(self, project_directory, db_type, orm, *blueprints):
        super(Project, self).__init__(project_directory)
        self.name = os.path.basename(self.directory)
        self.initialize_app(*blueprints)
        self.initialize_db(db_type, orm)

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, app):
        if type(app) is not App:
            raise TypeError("Object must be of type 'spill.App'")
        self._app = app

    @app.deleter
    def app(self):
        del self._app

    def initialize_app(self, *blueprints):
        self.app = App(self.directory, *blueprints)

    def initialize_db(self, db_type, orm):
        self.db = Database(self.directory, db_type, orm)

    def create_config_py(self):
        config_py = os.path.join(self.directory, 'config.py')
        self._write_template('config.jnj',
                             config_py,
                             project = self.as_dict())

    def create_gitignore(self):
        pass

    def create_manage_py(self):
        pass

    def create_readme(self):
        pass

    def create_requirements(self):
        pass

    def create_boilerplate(self):
        pass

    def create(self):
        pass

    def as_dict(self):
        return {
                'name': self.name,
                'db':   self.db.as_dict(),
                'app':  self.app.as_dict()
               }


class App(Scaffold):
    """
    The Flask application linked to a Project.
    """
    def __init__(self, directory, *blueprints):
        app_directory = os.path.join(directory, 'app')
        super(App, self).__init__(app_directory)
        self.blueprints = BlueprintList()
        for b in blueprints:
            blue = self.initalize_blueprint(b)
            self.blueprints.append(blue)

    def initalize_blueprint(self, blueprint_name):
        return Blueprint(self.directory, blueprint_name)

    def create(self):
        pass

    def as_dict(self):
        return {
                'directory': self.directory,
                'blueprints': [b.as_dict() for b in self.blueprints]
               }


class Blueprint(Scaffold):
    """
    A Flask blueprint, associated with an App.
    """
    def __init__(self, app_directory, name):
        blueprint_directory = os.path.join(app_directory, name)
        super(Blueprint, self).__init__(blueprint_directory)

    def create(self):
        pass

    def as_dict(self):
        return {
                'name':      self.name,
                'directory': self.directory
               }


class BlueprintList(MutableSequence):
    """
    A sequence, whose elements can only be Blueprint instances.
    http://stackoverflow.com/a/3488283
    """
    def __init__(self, *args):
        super(BlueprintList, self).__init__()
        self.list = list()
        self.extend(list(args))

    def __str__(self):
        return str(self.list)

    def __repr__(self):
        return str(self.list)

    def __len__(self):
        return len(self.list)

    def __getitem__(self, idx):
        return self.list[idx]

    def __delitem__(self, idx):
        del self.list[idx]

    def __setitem__(self, idx, element):
        self.check(element)
        self.list[idx] = element

    def check(self, element):
        if not isinstance(element, Blueprint):
            raise TypeError("A BlueprintList can only contain 'spill.Blueprint' objects")

    def insert(self, idx, element):
        self.check(element)
        self.list.insert(idx, element)


class Database(Scaffold):
    """
    The database linked to a Project.
    """
    def __init__(self, project_directory, db_type, orm):
        super(Database, self).__init__(project_directory)
        self.type = db_type.lower()
        self.orm  = orm.lower()

    def __repr__(self):
        return "Database(type=%s, orm=%s)" % (self.type, self.orm)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, db_type):
        if db_type not in SUPPORTED_DBS:
            raise Exception('Unsupported database type: %s', db_type)
        self._type = db_type

    @type.deleter
    def type(self):
        del self._type

    @property
    def orm(self):
        return self._orm

    @orm.setter
    def orm(self, orm):
        if orm not in SUPPORTED_ORMS:
            raise Exception('Unsupported orm: %s', orm)
        self._orm = orm

    @orm.deleter
    def orm(self):
        del self._orm

    def as_dict(self):
        return {
                'type': self.type,
                'orm':  self.orm
               }


class Test(object):
    """docstring for Blueprint"""
    def __init__(self, arg):
        super(Blueprint, self).__init__()
        self.arg = arg


def set_up_args(self):
    # Set up argument parsing
    parser = ap.ArgumentParser(description =
    """

    """)
    parser.add_argument('project',
                        nargs   = '?',
                        default = None,
                        help    = """Flask project to spill.""")
    parser.add_argument('-b', '--blueprints',
                        nargs = '+',
                        dest  = 'blueprints',
                        help  = "A list of blueprints to create")
    return parser.parse_args()

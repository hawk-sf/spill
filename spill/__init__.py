import os
import errno
import weakref
import argparse    as ap
from   jinja2      import Environment, PackageLoader
from   collections import MutableSequence

__version__ = '0.0.1'


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
SUPPORTED_DBS  = ['sqlite', 'mysql', 'mongodb']
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

    def spill(self):
        raise NotImplementedError


class Project(Scaffold):
    """
    A Flask project, composed of an app, a database, and tests.
    """
    def __init__(self, project_directory, *blueprints, **kwargs):
        super(Project, self).__init__(project_directory)
        self.name       = os.path.basename(self.directory)
        self.blueprints = blueprints
        self.models     = kwargs.get('models')
        self.forms      = kwargs.get('forms')
        self.templates  = kwargs.get('templates')
        self.config     = kwargs
        if self.templates:
            self.initialize_templates()
        self.initialize_db()
        self.initialize_app()

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

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, db):
        if type(db) is not Database:
            raise TypeError("Object must be of type 'spill.Database'")
        self._db = db

    @db.deleter
    def db(self):
        del self._db

    def as_dict(self):
        return {
                'name':      self.name,
                'db':        self.db.as_dict(),
                'app':       self.app.as_dict(),
                'models':    self.models,
                'forms':     self.forms,
                'templates': self.templates
               }

    def initialize_templates(self):
        mkdirs(os.path.join(self.directory, 'templates'))

    def initialize_app(self):
        self.app = App(self, *self.blueprints)

    def initialize_db(self):
        self.db = Database(self,
                           db_type = self.config.get('db_type'),
                           db_orm  = self.config.get('db_orm'))

    def create_config_py(self):
        config_py = os.path.join(self.directory, 'config.py')
        self._write_template('config.jnj',
                             config_py,
                             project = self.as_dict())

    def create_gitignore(self):
        gitignore = os.path.join(self.directory, '.gitignore')
        self._write_template('gitignore.jnj',
                             gitignore,
                             project = self.as_dict())

    def create_manage_py(self):
        manage_py = os.path.join(self.directory, 'manage.py')
        self._write_template('manage.jnj',
                             manage_py,
                             project = self.as_dict())

    def create_readme(self):
        readme_md = os.path.join(self.directory, 'README.md')
        self._write_template('readme.jnj',
                             readme_md,
                             project = self.as_dict())

    def create_requirements(self):
        requirements_txt = os.path.join(self.directory, 'requirements.txt')
        self._write_template('requirements.jnj',
                             requirements_txt,
                             project = self.as_dict())

    def _spill_boilerplate(self):
        self.create_config_py()
        self.create_gitignore()
        self.create_manage_py()
        self.create_readme()
        self.create_requirements()

    def spill(self):
        self._spill_boilerplate()
        self.app.spill()


class App(Scaffold):
    """
    The Flask application linked to a Project.
    """
    def __init__(self, project, *blueprints, **kwargs):
        self.project  = weakref.ref(project)
        app_directory = os.path.join(project.directory, 'app')
        super(App, self).__init__(app_directory)
        self.blueprints = BlueprintList()
        for b in blueprints:
            blue = self.initalize_blueprint(b)
            self.blueprints.append(blue)

    @property
    def project(self):
        return self._project()

    @project.setter
    def project(self, project):
        if type(project()) is not Project:
            raise TypeError("Object must be of type 'spill.Project'")
        self._project = project

    @project.deleter
    def project(self):
        del self._project

    def as_dict(self):
        return {
                'directory': self.directory,
                'blueprints': [b.as_dict() for b in self.blueprints]
               }

    def initalize_blueprint(self, blueprint_name):
        return Blueprint(self, blueprint_name)

    def create_init(self):
        app_init_py = os.path.join(self.directory, '__init__.py')
        self._write_template('app_init.jnj',
                             app_init_py,
                             project = self.project.as_dict())

    def create_models(self):
        models_py = os.path.join(self.directory, 'models.py')
        self._write_template('models.jnj',
                             models_py,
                             project = self.project.as_dict())

    def _spill_boilerplate(self):
        self.create_init()
        self.create_models()

    def _spill_blueprints(self):
        for blue in self.blueprints:
            blue.spill()

    def spill(self):
        self._spill_boilerplate()
        self._spill_blueprints()


class Blueprint(Scaffold):
    """
    A Flask blueprint, associated with an App.
    """
    def __init__(self, app, name):
        self.app            = weakref.ref(app)
        blueprint_directory = os.path.join(app.directory, name)
        super(Blueprint, self).__init__(blueprint_directory)

    @property
    def app(self):
        return self._app()

    @app.setter
    def app(self, app):
        if type(app()) is not App:
            raise TypeError("Object must be of type 'spill.App'")
        self._app = app

    @app.deleter
    def app(self):
        del self._app

    def as_dict(self):
        return {
                'name':      self.name,
                'directory': self.directory
               }

    def create_init(self):
        blueprint_init_py = os.path.join(self.directory, '__init__.py')
        self._write_template('blueprint_init.jnj',
                             blueprint_init_py,
                             blueprint = self.as_dict(),
                             project   = self.app.project.as_dict())

    def create_errors(self):
        blueprint_errors_py = os.path.join(self.directory, 'errors.py')
        self._write_template('blueprint_errors.jnj',
                             blueprint_errors_py,
                             blueprint = self.as_dict(),
                             project   = self.app.project.as_dict())

    def create_views(self):
        blueprint_views_py = os.path.join(self.directory, 'views.py')
        self._write_template('blueprint_views.jnj',
                             blueprint_views_py,
                             blueprint = self.as_dict(),
                             project   = self.app.project.as_dict())

    def create_forms(self):
        blueprint_forms_py = os.path.join(self.directory, 'forms.py')
        self._write_template('blueprint_forms.jnj',
                             blueprint_forms_py,
                             blueprint = self.as_dict(),
                             project   = self.app.project.as_dict())

    def spill(self):
        self.create_init()
        self.create_errors()
        self.create_views()


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
    def __init__(self, project, **kwargs):
        self.project  = weakref.ref(project)
        super(Database, self).__init__(project.directory)
        self.type = kwargs.get('db_type')
        self.orm  = kwargs.get('db_orm')

    def __repr__(self):
        return "Database(type=%s, orm=%s)" % (self.type, self.orm)

    @property
    def project(self):
        return self._project()

    @project.setter
    def project(self, project):
        if type(project()) is not Project:
            raise TypeError("Object must be of type 'spill.Project'")
        self._project = project

    @project.deleter
    def project(self):
        del self._project

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, db_type):
        if db_type is not None:
            if db_type not in SUPPORTED_DBS:
                raise Exception('Unsupported database type: %s', db_type)
            db_type = db_type.lower()
        self._type = db_type

    @type.deleter
    def type(self):
        del self._type

    @property
    def orm(self):
        return self._orm

    @orm.setter
    def orm(self, orm):
        if orm is not None:
            if orm not in SUPPORTED_ORMS:
                raise Exception('Unsupported orm: %s', orm)
            orm = orm.lower()
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


def set_up_args():
    parser = ap.ArgumentParser(formatter_class = ap.RawDescriptionHelpFormatter,
                               description     = """\
Creates scaffolding and boilerplate for a Flask application.

./<project>/
\t|-- .gitignore
\t|-- config.py
\t|-- manage.py
\t|-- README.md
\t|-- requirements.py
\t|-- /app
\t\t|-- __init__.py
\t\t|-- models.py
\t\t|-- /<blueprint_1>
\t\t\t|-- __init__.py
\t\t\t|-- errors.py
\t\t\t|-- forms.py
\t\t\t|-- views.py
\t\t|-- /<blueprint_2>
\t\t\t|-- __init__.py
\t\t\t|-- errors.py
\t\t\t|-- forms.py
\t\t\t|-- views.py
\t|-- /templates
""")

    parser.add_argument('project',
                        nargs   = '?',
                        default = os.getcwd(),
                        help    = "Name of Flask project to spill. If no project specified, will assume CWD is the project directory.")
    parser.add_argument('-b', '--blueprints',
                        nargs   = '+',
                        default = ['main', 'api'],
                        dest    = 'blueprints',
                        help    = "A list of blueprints to create (Defaults: 'main' and 'api')")
    parser.add_argument('-m', '--models',
                        nargs = '+',
                        dest  = 'models',
                        help  = "A list of model objects")
    parser.add_argument('--db-type',
                        dest    = 'db_type',
                        nargs   = '?',
                        choices = SUPPORTED_DBS,
                        help    = "The type of database you will use")
    parser.add_argument('--db-orm',
                        dest    = 'db_orm',
                        nargs   = '?',
                        choices = SUPPORTED_ORMS,
                        help    = "The ORM you will use")
    parser.add_argument('--no-forms',
                        action  = 'store_true',
                        help    = "No Flask-WTF forms")
    parser.add_argument('--no-templates',
                        action  = 'store_true',
                        help    = "No Jinja2 templates")
    return parser.parse_args()


def main():
    args = set_up_args()

    project = Project(args.project,
                      *args.blueprints,
                      models    = args.models,
                      db_type   = args.db_type,
                      db_orm    = args.db_orm,
                      forms     = not args.no_forms,
                      templates = not args.no_templates)
    project.spill()


if __name__ == '__main__':
    main()

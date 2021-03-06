Installation and Setup
======================

Requirements
'''''''''''''

* Python_ >= 2.7, with pip_ and virtualenv_   
* PostgreSQL_ >= 8.4
* RabbitMQ_ >= 2.6.1
* `Apache Solr`_

.. _Python: http://www.python.org/
.. _PostgreSQL: http://www.postgres.org/
.. _RabbitMQ: http://www.rabbitmq.com//
.. _Apache Solr: http://lucene.apache.org/solr/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _pip: http://pypi.python.org/pypi/pip

Installation
''''''''''''

First, check out the source code from the repository, e.g. via git on 
the command line::

    $ git clone http://github.com/okfn/openspending.git
    $ cd openspending

We also highly recommend you use a virtualenv_ to isolate the installed 
dependencies from the rest of your system.::

    $ virtualenv --no-site-packages ./pyenv

Now activate the environment. Your prompt will be prefixed with the name of
the environment.::

    $ source ./pyenv/bin/activate

Ensure that any in shell you use to complete the installation you have run the 
preceding command.

Having the virtualenv set up, you can install OpenSpending and its dependencies.
This should be pretty painless. Just run::

    $ pip install -E pyenv -e .

Another dependency is the ``openspendingjs`` module, which is included through
git submodules by initializing submodules from the root of the ``openspending``
install::

    $ git submodule init
    $ git submodule update 

You will also need to install python bindings for your database. For example,
for Postgresql you will want to install the psycopg2 library::

    pip install psycopg2
    # or on debian / ubuntu
    # apt-get install python-psycopg2


Create a database if you do not have one already. We recommend using Postgres
but you can use anything compatible with SQLAlchemy. For postgres you would do::

    createdb -E utf-8 --owner {your-database-user} openspending

Having done that, you can copy configuration templates::

    source pyenv/bin/activate
    cp development.ini_tmpl development.ini

Edit the configuration files to make sure you're pointing to a valid database 
URL is set::

    openspending.db.url = postgresql://{user}:{pass}@localhost/openspending

Initialize the database::

    ostool development.ini db init

Generate the help system documentation (this is used by the front-end
and must be available, developer documents are separate). The output 
will be copied to the web applications template directory::

    cd help; make clean html

Run the application::

    paster serve --reload development.ini

In order to use web-based importing and loading, you will also need to set up
the celery-based background daemon. When running this, make sure to have an
instance of RabbitMQ installed and running and then execute::

    paster celeryd development.ini

You can validate the functioning of the communication between the backend and
frontend components using the ping action::

    curl -q http://localhost:5000/__ping__ >/dev/null

This should result in "Pong!" being printed to the background daemon's console.

Installing optional plugins
'''''''''''''''''''''''''''

Additionally to the core software, there are a number of extensions that can 
be installed. These include: 

* Treemaps - support for displaying views as treemaps.
* DataTables - support for displaying views as tables.

To install these, it is recommended you create a file named ``pip-sources.txt``
with the following contents::

  -e git+http://github.com/okfn/openspending.plugins.treemap#egg=openspending.plugins.treemap
  -e git+http://github.com/okfn/openspending.plugins.datatables#egg=openspending.plugins.datatables

This can then be installed with a simple pip command:: 

  pip install -r pip-sources.txt

If you want to enable the plugins, also add the following directive to your
configuration file (e.g. ``development.ini``)::
  
  openspending.plugins = treemap datatables


Setup Solr
''''''''''

Create a configuration home directory to use with Solr. This is most easily 
done by copying the Solr example configuration from the `Solr tarball`_, and 
replacing the default schema with one from OpenSpending.::

    $ cp -R apache-solr-3.1.0/example/solr/* ./solr
    $ ln -sf "../openspending_schema.xml" ./solr/conf/schema.xml

.. _Solr tarball: http://www.apache.org/dyn/closer.cgi/lucene/solr/

Start Solr with the full path to the folder as a parameter: ::

    $ solr $(pwd)/solr


Customize the configuration file
''''''''''''''''''''''''''''''''

Create a configuration file, choosing a name that reflects the environment
in which this deployment will be used. For a development environment:::

    $ cp development.ini_tmpl development.ini

Edit the config file with relevant details for your local machine. The
options in the file are commented. Some of the important options in 
`[app:main]` are::
    
    # Configure your database. e.g. for a development database:
    openspending.db.url = postgresql://user:pass@host/dbname
    
    # Configure your Solr url. This is a typical default:
    openspending.solr.url = http://localhost:8983/solr
    
    # Choose which plugins to activate:
    openspending.plugins = treemap datatables [...]
    

Test the install and run the site
---------------------------------

Create test configuration (which inherits, by default, from `development.ini`): ::

    $ cp test.ini_tmpl test.ini

Run the tests.::

    $ nosetests 

Finally, run the site from development.ini::

    $ paster serve --reload development.ini

Create an Admin User
--------------------

On the web user interface, register as a normal user. Once signed up, go into 
the database and do (replacing your-name with your login name)::

  UPDATE "account" SET admin = true WHERE "name" = 'username';


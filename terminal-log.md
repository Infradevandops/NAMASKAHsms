
The default interactive shell is now zsh.
To update your account to use zsh, please run `chsh -s /bin/zsh`.
For more details, please visit https://support.apple.com/kb/HT208050.
bash-3.2$ ./start.sh
Starting Namaskah SMS...
Installing dependencies...
Running database migrations...
⚠️ Generated SECRET_KEY for development environment
⚠️ Generated JWT_SECRET_KEY for development environment
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 005_add_performance_indexes -> f6a9a9aafab3, Add soft delete columns
Traceback (most recent call last):
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: no such index: ix_rentals_status

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/usr/local/bin/alembic", line 7, in <module>
    sys.exit(main())
             ~~~~^^
  File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 1022, in main
    CommandLine(prog=prog).main(argv=argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 1012, in main
    self.run_cmd(cfg, options)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/alembic/config.py", line 946, in run_cmd
    fn(
    ~~^
        config,
        ^^^^^^^
        *[getattr(options, k, None) for k in positional],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        **{k: getattr(options, k, None) for k in kwarg},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/alembic/command.py", line 483, in upgrade
    script.run_env()
    ~~~~~~~~~~~~~~^^
  File "/usr/local/lib/python3.13/site-packages/alembic/script/base.py", line 545, in run_env
    util.load_python_file(self.dir, "env.py")
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 116, in load_python_file
    module = load_module_py(module_id, path)
  File "/usr/local/lib/python3.13/site-packages/alembic/util/pyfiles.py", line 136, in load_module_py
    spec.loader.exec_module(module)  # type: ignore
    ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "<frozen importlib._bootstrap_external>", line 1027, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/Users/machine/Desktop/Namaskah. app/alembic/env.py", line 74, in <module>
    run_migrations_online()
    ~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/machine/Desktop/Namaskah. app/alembic/env.py", line 68, in run_migrations_online
    context.run_migrations()
    ~~~~~~~~~~~~~~~~~~~~~~^^
  File "<string>", line 8, in run_migrations
  File "/usr/local/lib/python3.13/site-packages/alembic/runtime/environment.py", line 946, in run_migrations
    self.get_context().run_migrations(**kw)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/local/lib/python3.13/site-packages/alembic/runtime/migration.py", line 627, in run_migrations
    step.migration_fn(**kw)
    ~~~~~~~~~~~~~~~~~^^^^^^
  File "/Users/machine/Desktop/Namaskah. app/alembic/versions/f6a9a9aafab3_add_soft_delete_columns.py", line 21, in upgrade
    op.drop_index(op.f('ix_rentals_status'), table_name='rentals')
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<string>", line 8, in drop_index
  File "<string>", line 3, in drop_index
  File "/usr/local/lib/python3.13/site-packages/alembic/operations/ops.py", line 1142, in drop_index
    return operations.invoke(op)
           ~~~~~~~~~~~~~~~~~^^^^
  File "/usr/local/lib/python3.13/site-packages/alembic/operations/base.py", line 441, in invoke
    return fn(self, operation)
  File "/usr/local/lib/python3.13/site-packages/alembic/operations/toimpl.py", line 121, in drop_index
    operations.impl.drop_index(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^
        operation.to_index(operations.migration_context),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        **kw,
        ^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/alembic/ddl/impl.py", line 464, in drop_index
    self._exec(schema.DropIndex(index, **kw))
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/alembic/ddl/impl.py", line 246, in _exec
    return conn.execute(construct, params)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
    return meth(
        self,
        distilled_parameters,
        execution_options or NO_OPTIONS,
    )
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/sql/ddl.py", line 187, in _execute_on_connection
    return connection._execute_ddl(
           ~~~~~~~~~~~~~~~~~~~~~~~^
        self, distilled_params, execution_options
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1530, in _execute_ddl
    ret = self._execute_context(
        dialect,
    ...<4 lines>...
        compiled,
    )
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
    return self._exec_single_context(
           ~~~~~~~~~~~~~~~~~~~~~~~~~^
        dialect, context, statement, parameters
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
    self._handle_dbapi_exception(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        e, str_statement, effective_parameters, cursor, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/lib/python3.13/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such index: ix_rentals_status
[SQL: 
DROP INDEX ix_rentals_status]
(Background on this error at: https://sqlalche.me/e/20/e3q8)
Warning: Database migrations failed (may already be applied)
Creating default users...
/Users/machine/Desktop/Namaskah. app/.venv/bin/python: can't open file '/Users/machine/Desktop/Namaskah. app/create_users.py': [Errno 2] No such file or directory
Starting server on http://127.0.0.1:8000
See README.md for login credentials

INFO:     Will watch for changes in these directories: ['/Users/machine/Desktop/Namaskah. app']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [88343] using WatchFiles
⚠️ Generated SECRET_KEY for development environment
⚠️ Generated JWT_SECRET_KEY for development environment
Basic logging configured (structlog disabled for debugging)
2025-11-22 17:34:27,962 - startup - INFO - Running startup initialization
2025-11-22 17:34:28,026 - startup - INFO - Admin user verified and updated
2025-11-22 17:34:28,027 - startup - INFO - Startup initialization completed
INFO:     Started server process [88345]
INFO:     Waiting for application startup.
2025-11-22 17:34:28,142 - startup - INFO - Application startup
2025-11-22 17:34:28,291 - app.core.unified_cache - INFO - Redis cache connected
2025-11-22 17:34:28,310 - app.services.textverified_service - INFO - TextVerified client initialized successfully
INFO:     Application startup complete.
2025-11-22 17:34:28,312 - app.services.sms_polling_service - INFO - SMS polling service started
2025-11-22 17:34:28,323 - app.services.sms_polling_service - INFO - Started polling for verification bc9c8a80-c2aa-447e-b55f-5ad69e8cae75
2025-11-22 17:34:28,323 - app.services.sms_polling_service - INFO - Started polling for verification cdb4dbb7-bdc0-4cef-8d26-29685290bb99
2025-11-22 17:34:28,323 - app.services.sms_polling_service - INFO - Started polling for verification 992eed1a-60bf-4426-9646-277b5f4ae18b

2025-11-23T02:44:09.921071901Z     return self.main(*args, **kwargs)
2025-11-23T02:44:09.921116872Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.921189413Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-11-23T02:44:09.921409008Z     rv = self.invoke(ctx)
2025-11-23T02:44:09.921430418Z          ^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.92151219Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T02:44:09.921689534Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T02:44:09.921744565Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.921780816Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T02:44:09.92196653Z     return callback(*args, **kwargs)
2025-11-23T02:44:09.921996001Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.922061752Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T02:44:09.922181855Z     run(
2025-11-23T02:44:09.922186005Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T02:44:09.922319658Z     server.run()
2025-11-23T02:44:09.922327518Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T02:44:09.922458151Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T02:44:09.922550183Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.922557863Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T02:44:09.922718016Z     return runner.run(main)
2025-11-23T02:44:09.922805178Z            ^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.922811608Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T02:44:09.92290225Z     return self._loop.run_until_complete(task)
2025-11-23T02:44:09.92334309Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.92335356Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T02:44:09.923442192Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T02:44:09.923510143Z     config.load()
2025-11-23T02:44:09.923517274Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T02:44:09.923730688Z     self.loaded_app = import_from_string(self.app)
2025-11-23T02:44:09.923734368Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.923737248Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T02:44:09.923849341Z     module = importlib.import_module(module_str)
2025-11-23T02:44:09.923852501Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.923854791Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T02:44:09.923920742Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T02:44:09.924116066Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:44:09.924137477Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T02:44:09.924139997Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T02:44:09.924145627Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T02:44:09.924147957Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T02:44:09.924152487Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T02:44:09.924178808Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T02:44:09.924239749Z   File "/app/main.py", line 5, in <module>
2025-11-23T02:44:09.9242732Z     from app.core.startup import run_startup_initialization
2025-11-23T02:44:09.92427576Z   File "/app/app/core/startup.py", line 8, in <module>
2025-11-23T02:44:09.924338001Z     from app.core.auth_security import hash_password
2025-11-23T02:44:09.924343601Z   File "/app/app/core/auth_security.py", line 7, in <module>
2025-11-23T02:44:09.924437453Z     logger = get_logger("auth_security")
2025-11-23T02:44:09.924441433Z              ^^^^^^^^^^
2025-11-23T02:44:09.924539856Z NameError: name 'get_logger' is not defined
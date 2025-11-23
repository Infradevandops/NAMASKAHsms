2025-11-23T02:49:47.688943356Z     sys.exit(main())
2025-11-23T02:49:47.689010078Z              ^^^^^^
2025-11-23T02:49:47.689015518Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
2025-11-23T02:49:47.68937794Z     return self.main(*args, **kwargs)
2025-11-23T02:49:47.68939386Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.689399831Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-11-23T02:49:47.689742872Z     rv = self.invoke(ctx)
2025-11-23T02:49:47.689748672Z          ^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.689755532Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T02:49:47.690060082Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T02:49:47.690073192Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.690081562Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T02:49:47.779097057Z     return callback(*args, **kwargs)
2025-11-23T02:49:47.779134678Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.77918369Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T02:49:47.779325324Z     run(
2025-11-23T02:49:47.779330815Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T02:49:47.77947688Z     server.run()
2025-11-23T02:49:47.77948696Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T02:49:47.779576413Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T02:49:47.779642185Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.779656675Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T02:49:47.779786059Z     return runner.run(main)
2025-11-23T02:49:47.77980111Z            ^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.77980592Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T02:49:47.779904403Z     return self._loop.run_until_complete(task)
2025-11-23T02:49:47.779949264Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.779957475Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T02:49:47.78011179Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T02:49:47.780196663Z     config.load()
2025-11-23T02:49:47.780213463Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T02:49:47.780363048Z     self.loaded_app = import_from_string(self.app)
2025-11-23T02:49:47.78044221Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.78044722Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T02:49:47.780532453Z     module = importlib.import_module(module_str)
2025-11-23T02:49:47.780571664Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.780578125Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T02:49:47.780691208Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T02:49:47.780769271Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:49:47.780800732Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T02:49:47.780803962Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T02:49:47.780806482Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T02:49:47.780809392Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T02:49:47.780812032Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T02:49:47.780814912Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T02:49:47.780825652Z   File "/app/main.py", line 5, in <module>
2025-11-23T02:49:47.780897935Z     from app.core.startup import run_startup_initialization
2025-11-23T02:49:47.780910785Z   File "/app/app/core/startup.py", line 8, in <module>
2025-11-23T02:49:47.780977588Z     from app.core.auth_security import hash_password
2025-11-23T02:49:47.780991568Z ImportError: cannot import name 'hash_password' from 'app.core.auth_security' (/app/app/core/auth_security.py)
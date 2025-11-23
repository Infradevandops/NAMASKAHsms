2025-11-23T02:37:24.222589409Z              ^^^^^^
2025-11-23T02:37:24.2225922Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
2025-11-23T02:37:24.22259555Z     return self.main(*args, **kwargs)
2025-11-23T02:37:24.22259778Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.22260002Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-11-23T02:37:24.22260273Z     rv = self.invoke(ctx)
2025-11-23T02:37:24.22260495Z          ^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.2226072Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T02:37:24.22260938Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T02:37:24.22261166Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.22261389Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T02:37:24.2226161Z     return callback(*args, **kwargs)
2025-11-23T02:37:24.22261834Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.22262058Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T02:37:24.22262273Z     run(
2025-11-23T02:37:24.22262507Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T02:37:24.2226273Z     server.run()
2025-11-23T02:37:24.22262952Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T02:37:24.22263182Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T02:37:24.22263399Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.222636661Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T02:37:24.223797704Z     return runner.run(main)
2025-11-23T02:37:24.223807454Z            ^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.223810394Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T02:37:24.223813334Z     return self._loop.run_until_complete(task)
2025-11-23T02:37:24.223815744Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.223818164Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T02:37:24.223820964Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T02:37:24.223823534Z     config.load()
2025-11-23T02:37:24.223825794Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T02:37:24.223828824Z     self.loaded_app = import_from_string(self.app)
2025-11-23T02:37:24.223831114Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.223833864Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T02:37:24.223836184Z     module = importlib.import_module(module_str)
2025-11-23T02:37:24.223838374Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.223840694Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T02:37:24.224494687Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T02:37:24.224690351Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:37:24.224705422Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T02:37:24.224725492Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T02:37:24.224728502Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T02:37:24.224730862Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T02:37:24.224733142Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T02:37:24.224735462Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T02:37:24.224738082Z   File "/app/main.py", line 5, in <module>
2025-11-23T02:37:24.224802214Z     from app.core.startup import run_startup_initialization
2025-11-23T02:37:24.224822794Z   File "/app/app/core/startup.py", line 7, in <module>
2025-11-23T02:37:24.224889995Z     logger = get_logger("startup")
2025-11-23T02:37:24.224925846Z              ^^^^^^^^^^
2025-11-23T02:37:24.224962367Z NameError: name 'get_logger' is not defined
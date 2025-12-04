2025-12-04T18:29:47.451708924Z     sys.exit(main())
2025-12-04T18:29:47.451725915Z              ^^^^^^
2025-12-04T18:29:47.451738395Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
2025-12-04T18:29:47.452034601Z     return self.main(*args, **kwargs)
2025-12-04T18:29:47.452067451Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.452097042Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-12-04T18:29:47.452339767Z     rv = self.invoke(ctx)
2025-12-04T18:29:47.452358367Z          ^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.452364827Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-12-04T18:29:47.452588332Z     return ctx.invoke(self.callback, **ctx.params)
2025-12-04T18:29:47.452645703Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.452691044Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-12-04T18:29:47.452864027Z     return callback(*args, **kwargs)
2025-12-04T18:29:47.452923618Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.452973069Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-12-04T18:29:47.453083251Z     run(
2025-12-04T18:29:47.453088271Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-12-04T18:29:47.453181053Z     server.run()
2025-12-04T18:29:47.453185373Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-12-04T18:29:47.453268525Z     return asyncio.run(self.serve(sockets=sockets))
2025-12-04T18:29:47.453325936Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.453331026Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-12-04T18:29:47.453449458Z     return runner.run(main)
2025-12-04T18:29:47.453464329Z            ^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.453502139Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-12-04T18:29:47.453565651Z     return self._loop.run_until_complete(task)
2025-12-04T18:29:47.453611301Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.453621252Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-12-04T18:29:47.453752244Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-12-04T18:29:47.453834896Z     config.load()
2025-12-04T18:29:47.453850116Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-12-04T18:29:47.453979689Z     self.loaded_app = import_from_string(self.app)
2025-12-04T18:29:47.454018Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.45402438Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-12-04T18:29:47.454105151Z     module = importlib.import_module(module_str)
2025-12-04T18:29:47.454152012Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.454176372Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-12-04T18:29:47.454264344Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-12-04T18:29:47.454366236Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-04T18:29:47.454386137Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-12-04T18:29:47.454389217Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-12-04T18:29:47.454399877Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-12-04T18:29:47.454405767Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-12-04T18:29:47.454408577Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-12-04T18:29:47.454411697Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-12-04T18:29:47.454419627Z   File "/app/main.py", line 46, in <module>
2025-12-04T18:29:47.454505359Z     from app.api.verification.purchase_endpoints import router as purchase_router
2025-12-04T18:29:47.454512519Z   File "/app/app/api/verification/purchase_endpoints.py", line 15, in <module>
2025-12-04T18:29:47.45458994Z     from app.schemas.verification import VerificationRequest
2025-12-04T18:29:47.454601681Z ImportError: cannot import name 'VerificationRequest' from 'app.schemas.verification' (/app/app/schemas/verification.py)
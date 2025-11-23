2025-11-23T03:14:19.977204747Z     rv = self.invoke(ctx)
2025-11-23T03:14:19.977230788Z          ^^^^^^^^^^^^^^^^
2025-11-23T03:14:19.977240419Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T03:14:20.06301042Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T03:14:20.063165118Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.063174309Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T03:14:20.063525518Z     return callback(*args, **kwargs)
2025-11-23T03:14:20.06356135Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.063588171Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T03:14:20.063733599Z     run(
2025-11-23T03:14:20.063742089Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T03:14:20.063902818Z     server.run()
2025-11-23T03:14:20.063924019Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T03:14:20.063994823Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T03:14:20.064106519Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.064118749Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T03:14:20.064216065Z     return runner.run(main)
2025-11-23T03:14:20.064244746Z            ^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.064279758Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T03:14:20.064360242Z     return self._loop.run_until_complete(task)
2025-11-23T03:14:20.064415325Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.064422505Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T03:14:20.064588204Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T03:14:20.064655628Z     config.load()
2025-11-23T03:14:20.064724112Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T03:14:20.064847288Z     self.loaded_app = import_from_string(self.app)
2025-11-23T03:14:20.064899581Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.064908582Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T03:14:20.065003747Z     module = importlib.import_module(module_str)
2025-11-23T03:14:20.06506253Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.06507347Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T03:14:20.065180826Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T03:14:20.065272671Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T03:14:20.065294362Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T03:14:20.065298202Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T03:14:20.065300692Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T03:14:20.065306183Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T03:14:20.065308813Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T03:14:20.065311573Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T03:14:20.065318443Z   File "/app/main.py", line 6, in <module>
2025-11-23T03:14:20.065405938Z     from app.middleware.csrf_middleware import CSRFMiddleware
2025-11-23T03:14:20.065430859Z   File "/app/app/middleware/__init__.py", line 13, in <module>
2025-11-23T03:14:20.065534535Z     from .security import (
2025-11-23T03:14:20.065544476Z   File "/app/app/middleware/security.py", line 11, in <module>
2025-11-23T03:14:20.06562422Z     from app.services.auth import AuthService
2025-11-23T03:14:20.06563778Z   File "/app/app/services/__init__.py", line 4, in <module>
2025-11-23T03:14:20.065710954Z     from .auth_service import AuthService
2025-11-23T03:14:20.065718685Z   File "/app/app/services/auth_service.py", line 8
2025-11-23T03:14:20.065721355Z     create_access_token,
2025-11-23T03:14:20.065723105Z IndentationError: unexpected indent
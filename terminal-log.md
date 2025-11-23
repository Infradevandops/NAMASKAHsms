2025-11-23T02:58:56.163737999Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-11-23T02:58:56.164087995Z     rv = self.invoke(ctx)
2025-11-23T02:58:56.164114546Z          ^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.164135546Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-11-23T02:58:56.164422362Z     return ctx.invoke(self.callback, **ctx.params)
2025-11-23T02:58:56.164501894Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.164512124Z   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-11-23T02:58:56.164717228Z     return callback(*args, **kwargs)
2025-11-23T02:58:56.16479794Z            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.16482853Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 416, in main
2025-11-23T02:58:56.164979733Z     run(
2025-11-23T02:58:56.164987893Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-11-23T02:58:56.165155776Z     server.run()
2025-11-23T02:58:56.165163897Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
2025-11-23T02:58:56.165265439Z     return asyncio.run(self.serve(sockets=sockets))
2025-11-23T02:58:56.16532581Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.165379791Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-11-23T02:58:56.169261388Z     return runner.run(main)
2025-11-23T02:58:56.169281698Z            ^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.169290338Z   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-11-23T02:58:56.16940674Z     return self._loop.run_until_complete(task)
2025-11-23T02:58:56.169470682Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.169480902Z   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-11-23T02:58:56.169656125Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
2025-11-23T02:58:56.169753087Z     config.load()
2025-11-23T02:58:56.169761778Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 467, in load
2025-11-23T02:58:56.169928221Z     self.loaded_app = import_from_string(self.app)
2025-11-23T02:58:56.170033143Z                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.170041883Z   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-11-23T02:58:56.170097874Z     module = importlib.import_module(module_str)
2025-11-23T02:58:56.170177446Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.170189866Z   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-11-23T02:58:56.17545549Z     return _bootstrap._gcd_import(name[level:], package, level)
2025-11-23T02:58:56.175524321Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-23T02:58:56.175548332Z   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-11-23T02:58:56.175551862Z   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-11-23T02:58:56.175555062Z   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-11-23T02:58:56.175560112Z   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-11-23T02:58:56.175566712Z   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-11-23T02:58:56.175569742Z   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-11-23T02:58:56.175572672Z   File "/app/main.py", line 6, in <module>
2025-11-23T02:58:56.175696585Z     from app.middleware.csrf_middleware import CSRFMiddleware
2025-11-23T02:58:56.175712805Z   File "/app/app/middleware/__init__.py", line 5, in <module>
2025-11-23T02:58:56.175792817Z     from .logging import (
2025-11-23T02:58:56.175797367Z   File "/app/app/middleware/logging.py", line 15, in <module>
2025-11-23T02:58:56.175932229Z     class RequestLoggingMiddleware(BaseHTTPMiddleware):
2025-11-23T02:58:56.17594116Z   File "/app/app/middleware/logging.py", line 127, in RequestLoggingMiddleware
2025-11-23T02:58:56.176015771Z     def _log_response(request: Request, response: Response, process_time: float):
2025-11-23T02:58:56.176096913Z                                                   ^^^^^^^^
2025-11-23T02:58:56.176184514Z NameError: name 'Response' is not defined